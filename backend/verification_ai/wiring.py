"""
verification_ai/wiring.py
─────────────────────────
Central helper called by supplier and consumer routers after a handoff
record is saved.  Loads all available handoff records for a shipment,
builds PartyReport objects, runs the cross-match engine, writes an
AIFlag row to the DB, and dispatches the blockchain BackgroundTask.

Rules (from master prompt):
  • < 2 handoffs   → return PENDING, no AIFlag written yet
  • 2 or 3 parties → run cross-match
  • FLAGGED        → call blockchain_service.flag_shipment()
  • VERIFIED       → add bg_record_handoff_and_store as BackgroundTask
  • Always write AIFlag to DB when we have >= 2 parties
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from models import AIFlag, HandoffRecord, MedicineBatch, Shipment
from verification_ai.engine import PartyReport, run_verification

logger = logging.getLogger(__name__)

# Stage name → which PartyReport field it fills
_STAGE_ROLE = {
    "manufacturer_dispatch": "manufacturer",
    "supplier_receipt":      "supplier",
    "hospital_receipt":      "hospital",
}


def _load_party_reports(
    db: Session, shipment_id: str, batch: MedicineBatch
) -> tuple[Optional[PartyReport], Optional[PartyReport], Optional[PartyReport]]:
    """
    Load all HandoffRecords for a shipment and build PartyReport objects.
    Returns (manufacturer_report, supplier_report, hospital_report).
    Any party that hasn't submitted yet will be None.
    """
    handoffs = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.shipment_id == shipment_id)
        .all()
    )

    reports: dict[str, PartyReport] = {}
    for h in handoffs:
        role = _STAGE_ROLE.get(h.stage)
        if role is None:
            continue
        reports[role] = PartyReport(
            party=role,
            quantity=h.quantity_reported,
            expiry=h.expiry_reported if isinstance(h.expiry_reported, datetime) else None,
            temp=h.temp_reported,
        )

    # If supplier handoff is missing (because it's attached to the previous shipment)
    if "supplier" not in reports:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if shipment:
            sup_incoming = (
                db.query(Shipment)
                .filter(
                    Shipment.batch_id == shipment.batch_id,
                    Shipment.to_entity_id == shipment.from_entity_id
                )
                .first()
            )
            if sup_incoming:
                sup_handoff = (
                    db.query(HandoffRecord)
                    .filter(
                        HandoffRecord.shipment_id == sup_incoming.id,
                        HandoffRecord.stage == "supplier_receipt"
                    )
                    .first()
                )
                if sup_handoff:
                    reports["supplier"] = PartyReport(
                        party="supplier",
                        quantity=sup_handoff.quantity_reported,
                        expiry=sup_handoff.expiry_reported if isinstance(sup_handoff.expiry_reported, datetime) else None,
                        temp=sup_handoff.temp_reported,
                    )

    # Manufacturer report: if no explicit manufacturer handoff, use batch data
    if "manufacturer" not in reports:
        reports["manufacturer"] = PartyReport(
            party="manufacturer",
            quantity=batch.quantity,
            expiry=batch.expiry_date if isinstance(batch.expiry_date, datetime) else None,
            temp=batch.storage_temp_declared,
        )

    return (
        reports.get("manufacturer"),
        reports.get("supplier"),
        reports.get("hospital"),
    )


def trigger_verification_and_blockchain(
    shipment_id: str,
    db: Session,
    background_tasks: BackgroundTasks,
    hospital_shipment_id: Optional[str] = None,
) -> dict:
    """
    Called from supplier/router.py and consumer/router.py after a handoff
    record is saved.

    Returns a dict with keys: status, risk_score, explanation, ai_flag_id
    """
    from blockchain_service.service import bg_record_handoff_and_store, get_blockchain_service
    from database import SessionLocal

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        logger.warning("trigger_verification: shipment %s not found", shipment_id)
        return {"status": "PENDING", "risk_score": 0, "explanation": "Shipment not found", "ai_flag_id": None}

    batch = db.query(MedicineBatch).filter(MedicineBatch.id == shipment.batch_id).first()
    if not batch:
        logger.warning("trigger_verification: batch not found for shipment %s", shipment_id)
        return {"status": "PENDING", "risk_score": 0, "explanation": "Batch not found", "ai_flag_id": None}

    mfr, sup, hos = _load_party_reports(db, shipment_id, batch)

    # Need at least supplier + hospital to cross-match (manufacturer data always available from batch)
    if sup is None or hos is None:
        missing = []
        if sup is None:
            missing.append("supplier")
        if hos is None:
            missing.append("hospital")
        return {
            "status": "PENDING",
            "risk_score": 0,
            "explanation": f"Waiting for: {', '.join(missing)}",
            "ai_flag_id": None,
        }

    # Find supplier_dispatched from outbound shipment if available
    supplier_dispatched: Optional[int] = None
    # Look for an outbound shipment from supplier to hospital for this batch
    outbound = (
        db.query(Shipment)
        .filter(
            Shipment.batch_id == shipment.batch_id,
            Shipment.from_entity_id == shipment.to_entity_id,  # supplier is the from
        )
        .first()
    )
    if outbound and outbound.quantity_dispatched:
        supplier_dispatched = outbound.quantity_dispatched

    result = run_verification(
        manufacturer=mfr,
        supplier=sup,
        hospital=hos,
        hospital_shipment_id=hospital_shipment_id or shipment_id,
        supplier_dispatched=supplier_dispatched,
    )

    # Write AIFlag record
    ai_flag = AIFlag(
        shipment_id=shipment_id,
        risk_score=result.risk_score,
        status=result.status,
        triggered_rules=result.triggered_rules_json(),
        mismatch_details=result.mismatch_details_json(),
        explanation=result.explanation,
    )
    db.add(ai_flag)
    db.flush()

    logger.info(
        "AIFlag written for shipment %s: status=%s risk=%.0f",
        shipment_id, result.status, result.risk_score,
    )

    # Blockchain actions
    bc_svc = get_blockchain_service()
    
    # Always record handoff on-chain so the tx hash is saved to the DB
    background_tasks.add_task(
        bg_record_handoff_and_store,
        shipment_id,
        result.status,
        result.risk_score,
        SessionLocal,
        Shipment,
        shipment_id,
        "blockchain_hash",
    )
    logger.info("Queued blockchain handoff record for shipment %s", shipment_id)

    if result.status == "FLAGGED":
        background_tasks.add_task(
            bc_svc.flag_shipment, shipment_id, result.explanation[:200]
        )
        logger.info("Queued blockchain flag for shipment %s", shipment_id)

    return {
        "status": result.status,
        "risk_score": result.risk_score,
        "explanation": result.explanation,
        "ai_flag_id": ai_flag.id,
    }
