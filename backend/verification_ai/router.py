import json
from typing import List, Optional, Tuple
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import MedicineBatch, Supplier, Consumer, Manufacturer, Shipment, HandoffRecord, AIFlag
from auth.dependencies import get_current_user
from verification_ai.engine import PartyReport, run_verification
from verification_ai.schemas import (
    VerificationResponse, PartySnapshot, FlagListItem,
    LegReport, RoleVerificationResponse,
)
from verification_ai.leg_builder import build_leg
from trust_engine.engine import update_trust_after_verification
from blockchain_service.service import bg_record_handoff_and_store

router = APIRouter(prefix="/verification-ai", tags=["Verification AI"])


def _get_handoff_for_batch(
    db: Session, batch_id: str, stage: str
) -> Optional[Tuple[HandoffRecord, Shipment]]:
    row = (
        db.query(HandoffRecord, Shipment)
        .join(Shipment, HandoffRecord.shipment_id == Shipment.id)
        .filter(Shipment.batch_id == batch_id, HandoffRecord.stage == stage)
        .order_by(HandoffRecord.submitted_at.desc())
        .first()
    )
    return row


def _party_from_handoff(party: str, handoff: HandoffRecord) -> PartyReport:
    return PartyReport(
        party=party,
        quantity=handoff.quantity_reported,
        expiry=handoff.expiry_reported,
        temp=handoff.temp_reported,
    )


def _to_snapshot(report: PartyReport) -> PartySnapshot:
    return PartySnapshot(
        party=report.party,
        quantity=report.quantity,
        expiry=report.expiry,
        temp=report.temp,
    )


def _build_response(
    batch: MedicineBatch,
    result,
    flag: Optional[AIFlag],
    manufacturer: PartyReport,
    supplier: Optional[PartyReport],
    hospital: Optional[PartyReport],
) -> VerificationResponse:
    return VerificationResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        medicine_name=batch.name,
        shipment_id=result.hospital_shipment_id,
        flag_id=flag.id if flag else None,
        status=result.status,
        risk_score=result.risk_score,
        triggered_rules=result.triggered_rules,
        mismatch_details=result.mismatches,
        explanation=result.explanation,
        manufacturer=_to_snapshot(manufacturer),
        supplier=_to_snapshot(supplier) if supplier else None,
        hospital=_to_snapshot(hospital) if hospital else None,
    )


@router.post("/batches/{batch_id}/verify", response_model=VerificationResponse)
def verify_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    supplier_row = _get_handoff_for_batch(db, batch_id, "supplier_receipt")
    hospital_row = _get_handoff_for_batch(db, batch_id, "hospital_receipt")

    mfg_qty = batch.quantity
    if supplier_row:
        supplier_shipment = supplier_row[1]
        if supplier_shipment.quantity_dispatched is not None:
            mfg_qty = supplier_shipment.quantity_dispatched

    manufacturer = PartyReport(
        party="manufacturer",
        quantity=mfg_qty,
        expiry=batch.expiry_date,
        temp=batch.storage_temp_declared,
        batch_name=batch.name,
        batch_number=batch.batch_number,
    )

    supplier = (
        _party_from_handoff("supplier", supplier_row[0]) if supplier_row else None
    )
    hospital = (
        _party_from_handoff("hospital", hospital_row[0]) if hospital_row else None
    )
    hospital_shipment_id = hospital_row[1].id if hospital_row else None
    supplier_dispatched = hospital_row[1].quantity_dispatched if hospital_row else None

    result = run_verification(
        manufacturer=manufacturer,
        supplier=supplier,
        hospital=hospital,
        hospital_shipment_id=hospital_shipment_id,
        supplier_dispatched=supplier_dispatched,
    )

    flag = None
    if result.hospital_shipment_id and result.status != "PENDING":
        flag = AIFlag(
            shipment_id=result.hospital_shipment_id,
            risk_score=result.risk_score,
            status=result.status,
            triggered_rules=result.triggered_rules_json(),
            mismatch_details=result.mismatch_details_json(),
            explanation=result.explanation,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)

        # ── Trust Engine: update entity trust scores ──────────────────────────
        update_trust_after_verification(
            db=db,
            shipment_id=result.hospital_shipment_id,
            ai_status=result.status,
            risk_score=result.risk_score,
        )

        # ── Blockchain: async record handoff on-chain ─────────────────────────
        # BackgroundTask runs AFTER response is sent — never blocks the API.
        # Writes tx hash back to shipment.blockchain_hash in DB.
        background_tasks.add_task(
            bg_record_handoff_and_store,
            shipment_id=result.hospital_shipment_id,
            status=result.status,
            risk_score=result.risk_score,
            db_session_factory=SessionLocal,
            model_class=Shipment,
            record_id=result.hospital_shipment_id,
            hash_column="blockchain_hash",
        )

        # Also update the batch's blockchain_hash
        background_tasks.add_task(
            bg_record_handoff_and_store,
            shipment_id=result.hospital_shipment_id,
            status=result.status,
            risk_score=result.risk_score,
            db_session_factory=SessionLocal,
            model_class=MedicineBatch,
            record_id=batch_id,
            hash_column="blockchain_hash",
        )

    elif result.hospital_shipment_id and result.status == "PENDING":
        flag = (
            db.query(AIFlag)
            .filter(AIFlag.shipment_id == result.hospital_shipment_id)
            .order_by(AIFlag.created_at.desc())
            .first()
        )

    return _build_response(batch, result, flag, manufacturer, supplier, hospital)


@router.get("/batches/{batch_id}", response_model=VerificationResponse)
def get_batch_verification(
    batch_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    manufacturer = PartyReport(
        party="manufacturer",
        quantity=batch.quantity,
        expiry=batch.expiry_date,
        temp=batch.storage_temp_declared,
    )
    supplier_row = _get_handoff_for_batch(db, batch_id, "supplier_receipt")
    hospital_row = _get_handoff_for_batch(db, batch_id, "hospital_receipt")
    supplier = (
        _party_from_handoff("supplier", supplier_row[0]) if supplier_row else None
    )
    hospital = (
        _party_from_handoff("hospital", hospital_row[0]) if hospital_row else None
    )
    hospital_shipment_id = hospital_row[1].id if hospital_row else None
    supplier_dispatched = hospital_row[1].quantity_dispatched if hospital_row else None

    result = run_verification(
        manufacturer, supplier, hospital, hospital_shipment_id, supplier_dispatched
    )

    flag = None
    if hospital_shipment_id:
        flag = (
            db.query(AIFlag)
            .filter(AIFlag.shipment_id == hospital_shipment_id)
            .order_by(AIFlag.created_at.desc())
            .first()
        )

    return _build_response(batch, result, flag, manufacturer, supplier, hospital)


@router.get("/flags", response_model=List[FlagListItem])
def list_flags(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = (
        db.query(AIFlag, Shipment, MedicineBatch)
        .join(Shipment, AIFlag.shipment_id == Shipment.id)
        .join(MedicineBatch, Shipment.batch_id == MedicineBatch.id)
        .order_by(AIFlag.created_at.desc())
    )
    if status_filter:
        query = query.filter(AIFlag.status == status_filter.upper())

    rows = query.limit(min(limit, 100)).all()
    items = []
    for flag, shipment, batch in rows:
        rules = []
        if flag.triggered_rules:
            try:
                rules = json.loads(flag.triggered_rules)
            except json.JSONDecodeError:
                rules = [flag.triggered_rules]
        items.append(
            FlagListItem(
                id=flag.id,
                shipment_id=shipment.id,
                batch_id=batch.id,
                batch_number=batch.batch_number,
                medicine_name=batch.name,
                risk_score=flag.risk_score or 0,
                status=flag.status,
                explanation=flag.explanation,
                created_at=flag.created_at,
            )
        )
    return items


# ── Role-specific endpoint helpers (manufacturer / supplier / hospital) ────────
from verification_ai.leg_builder import build_leg as _build_leg
from verification_ai.schemas import RoleVerificationResponse as _RoleVR


def _overall(legs: list) -> tuple:
    """Derive overall_status + risk from legs. LOW_DEVIATION surfaces small gaps."""
    has_flag = any(
        leg.qty_status in ("DEVIATION", "LOW_DEVIATION")
        or leg.expiry_status == "MISMATCH"
        or leg.temp_status == "DEVIATION"
        for leg in legs
    )
    has_pending = any(
        leg.qty_status == "PENDING" or leg.expiry_status == "PENDING"
        for leg in legs
    )
    if has_flag:
        risk = sum(
            (30 if leg.qty_status == "DEVIATION" else 10 if leg.qty_status == "LOW_DEVIATION" else 0)
            + (40 if leg.expiry_status == "MISMATCH" else 0)
            + (15 if leg.temp_status == "DEVIATION" else 0)
            for leg in legs
        )
        return "FLAGGED", min(100.0, float(risk))
    if has_pending:
        return "PENDING", 0.0
    return "VERIFIED", 0.0


# ── Manufacturer: full chain view ─────────────────────────────────────────────

@router.get(
    "/manufacturer/batch/{batch_id}",
    response_model=_RoleVR,
    summary="Manufacturer full-chain verification view",
)
def manufacturer_chain_view(
    batch_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    legs = []
    mfr_shipments = (
        db.query(Shipment)
        .filter(Shipment.batch_id == batch_id, Shipment.from_entity_id == batch.manufacturer_id)
        .order_by(Shipment.created_at)
        .all()
    )

    for mfr_ship in mfr_shipments:
        sup_handoff = (
            db.query(HandoffRecord)
            .filter(HandoffRecord.shipment_id == mfr_ship.id,
                    HandoffRecord.stage == "supplier_receipt")
            .first()
        )
        sup_entity = db.query(Supplier).filter(Supplier.id == mfr_ship.to_entity_id).first()
        sup_name = sup_entity.name if sup_entity else "Supplier"
        legs.append(_build_leg("manufacturer_to_supplier", "Manufacturer", sup_name,
                               mfr_ship, batch, sup_handoff))
        if sup_entity:
            for sup_ship in (
                db.query(Shipment)
                .filter(Shipment.batch_id == batch_id,
                        Shipment.from_entity_id == sup_entity.id)
                .order_by(Shipment.created_at)
                .all()
            ):
                hosp_handoff = (
                    db.query(HandoffRecord)
                    .filter(HandoffRecord.shipment_id == sup_ship.id,
                            HandoffRecord.stage == "hospital_receipt")
                    .first()
                )
                hosp_entity = db.query(Consumer).filter(Consumer.id == sup_ship.to_entity_id).first()
                hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"
                legs.append(_build_leg("supplier_to_hospital", sup_name, hosp_name,
                                       sup_ship, batch, hosp_handoff))

    overall_status, risk = _overall(legs)
    if not legs:
        summary = "Batch {} — {:,} units produced. No outbound shipments yet.".format(
            batch.batch_number, batch.quantity or 0)
    elif overall_status == "VERIFIED":
        summary = "Full chain verified. Batch {} — {:,} units. All {} leg(s) cleared.".format(
            batch.batch_number, batch.quantity or 0, len(legs))
    elif overall_status == "FLAGGED":
        flag = db.query(AIFlag).join(Shipment).filter(Shipment.batch_id == batch_id).order_by(AIFlag.created_at.desc()).first()
        if flag and flag.explanation:
            summary = flag.explanation
        else:
            summary = "Chain discrepancy detected. Risk {:.0f}/100. Review legs below.".format(risk)
    else:
        summary = "Pending — waiting for handoff confirmations from downstream parties."

    return _RoleVR(
        role="manufacturer", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=legs, overall_status=overall_status, risk_score=risk, summary=summary,
    )


# ── Supplier: incoming + outgoing legs ────────────────────────────────────────

@router.get(
    "/supplier/shipment/{incoming_shipment_id}",
    response_model=_RoleVR,
    summary="Supplier two-leg chain view",
)
def supplier_chain_view(
    incoming_shipment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    incoming = db.query(Shipment).filter(Shipment.id == incoming_shipment_id).first()
    if not incoming:
        raise HTTPException(status_code=404, detail="Incoming shipment not found")
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == incoming.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    mfr_entity = db.query(Manufacturer).filter(Manufacturer.id == incoming.from_entity_id).first()
    mfr_name = mfr_entity.name if mfr_entity else "Manufacturer"
    sup_entity = db.query(Supplier).filter(Supplier.id == incoming.to_entity_id).first()
    sup_name = sup_entity.name if sup_entity else "Supplier"

    sup_handoff = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.shipment_id == incoming.id,
                HandoffRecord.stage == "supplier_receipt")
        .first()
    )
    legs = [_build_leg("manufacturer_to_supplier", mfr_name, sup_name,
                       incoming, batch, sup_handoff)]

    if sup_entity:
        for sup_ship in (
            db.query(Shipment)
            .filter(Shipment.batch_id == batch.id,
                    Shipment.from_entity_id == sup_entity.id)
            .order_by(Shipment.created_at)
            .all()
        ):
            hosp_handoff = (
                db.query(HandoffRecord)
                .filter(HandoffRecord.shipment_id == sup_ship.id,
                        HandoffRecord.stage == "hospital_receipt")
                .first()
            )
            hosp_entity = db.query(Consumer).filter(Consumer.id == sup_ship.to_entity_id).first()
            hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"
            legs.append(_build_leg("supplier_to_hospital", sup_name, hosp_name,
                                   sup_ship, batch, hosp_handoff))

    overall_status, risk = _overall(legs)
    if overall_status == "VERIFIED":
        summary = "Both legs verified. Received from {}: {:,} units. Downstream confirmed.".format(
            mfr_name, incoming.quantity_dispatched or 0)
    elif overall_status == "FLAGGED":
        flag = db.query(AIFlag).filter(AIFlag.shipment_id == incoming.id).order_by(AIFlag.created_at.desc()).first()
        if flag and flag.explanation:
            summary = flag.explanation
        else:
            summary = "Shipment flagged. Risk {:.0f}/100. Discrepancy logged.".format(risk)
    else:
        summary = "Awaiting downstream confirmation from hospital."

    return _RoleVR(
        role="supplier", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=legs, overall_status=overall_status, risk_score=risk, summary=summary,
    )


# ── Hospital: single leg + batch identity ─────────────────────────────────────

@router.get(
    "/hospital/shipment/{incoming_shipment_id}",
    response_model=_RoleVR,
    summary="Hospital/consumer authenticity check",
)
def hospital_chain_view(
    incoming_shipment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    incoming = db.query(Shipment).filter(Shipment.id == incoming_shipment_id).first()
    if not incoming:
        raise HTTPException(status_code=404, detail="Incoming shipment not found")
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == incoming.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    sup_entity = db.query(Supplier).filter(Supplier.id == incoming.from_entity_id).first()
    sup_name = sup_entity.name if sup_entity else "Supplier"
    hosp_entity = db.query(Consumer).filter(Consumer.id == incoming.to_entity_id).first()
    hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"

    hosp_handoff = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.shipment_id == incoming.id,
                HandoffRecord.stage == "hospital_receipt")
        .first()
    )
    leg = _build_leg("supplier_to_hospital", sup_name, hosp_name,
                     incoming, batch, hosp_handoff)
    overall_status, risk = _overall([leg])

    if overall_status == "VERIFIED":
        qty = hosp_handoff.quantity_reported if hosp_handoff else 0
        exp = batch.expiry_date.date() if batch.expiry_date else "—"
        summary = ("Shipment {} verified. Received {:,} units of {} (Batch #{}). "
                   "Expiry {}. Product identity: authentic.").format(
            incoming.shipment_code, qty, batch.name, batch.batch_number, exp)
    elif overall_status == "FLAGGED":
        summary = ("Discrepancy in received shipment. Risk {:.0f}/100. "
                   "Do not distribute until resolved.").format(risk)
    else:
        summary = "Submit your receipt confirmation to run the verification check."

    return _RoleVR(
        role="consumer", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=[leg], overall_status=overall_status, risk_score=risk, summary=summary,
    )
