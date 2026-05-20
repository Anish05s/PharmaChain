"""
leg_builder.py
Shared helper: builds a LegReport from a shipment + handoff pair.
Used by the manufacturer, supplier, and hospital verification endpoints.
"""
from datetime import datetime
from typing import Optional
from models import Shipment, HandoffRecord, MedicineBatch
from verification_ai.schemas import LegReport

QUANTITY_THRESHOLD = 0.15      # > 15% → DEVIATION (flagged hard)
QUANTITY_LOW_THRESHOLD = 0.0  # > 0% but <= 15% → LOW_DEVIATION (flagged soft)
TEMP_TOLERANCE = 5.0


def _pct(expected: int, actual: int) -> float:
    if expected == 0:
        return 0.0
    return abs(actual - expected) / expected


def build_leg(
    leg_name: str,
    from_party: str,
    to_party: str,
    shipment: Shipment,
    batch: MedicineBatch,
    handoff: Optional[HandoffRecord],
) -> LegReport:
    dispatched = shipment.quantity_dispatched or 0

    # ── quantity ────────────────────────────────────────────────────────────
    if handoff is None or handoff.quantity_reported is None:
        qty_status = "PENDING"
        qty_dev = None
        received_qty = None
    else:
        received_qty = handoff.quantity_reported
        dev = _pct(dispatched, received_qty)
        qty_dev = round(dev * 100, 2)
        if dev > QUANTITY_THRESHOLD:
            qty_status = "DEVIATION"
        elif dev > QUANTITY_LOW_THRESHOLD:
            qty_status = "LOW_DEVIATION"
        else:
            qty_status = "MATCH"

    # ── expiry ──────────────────────────────────────────────────────────────
    if handoff is None or handoff.expiry_reported is None:
        expiry_status = "PENDING"
        received_expiry = None
    else:
        received_expiry = handoff.expiry_reported
        same = (
            batch.expiry_date is not None
            and received_expiry.date() == batch.expiry_date.date()
        )
        expiry_status = "MATCH" if same else "MISMATCH"

    # ── temperature ─────────────────────────────────────────────────────────
    if handoff is None or handoff.temp_reported is None:
        temp_status = "N/A"
        temp_dev = None
        received_temp = None
    elif batch.storage_temp_declared is None:
        temp_status = "N/A"
        temp_dev = None
        received_temp = handoff.temp_reported
    else:
        received_temp = handoff.temp_reported
        temp_dev = round(abs(received_temp - batch.storage_temp_declared), 1)
        temp_status = "DEVIATION" if temp_dev > TEMP_TOLERANCE else "MATCH"

    # ── human-readable notes ─────────────────────────────────────────────────
    notes_parts = []
    if qty_status == "MATCH":
        notes_parts.append("Qty {} dispatched = {} received".format(
            f"{dispatched:,}", f"{received_qty:,}"))
    elif qty_status == "LOW_DEVIATION":
        missing = abs((received_qty or 0) - dispatched)
        notes_parts.append(
            "Qty ⚠ dispatched {:,} but received {:,} ({} units short, {:.2f}% deviation)".format(
                dispatched, received_qty or 0, missing, qty_dev)
        )
    elif qty_status == "DEVIATION":
        missing = abs((received_qty or 0) - dispatched)
        notes_parts.append(
            "Qty 🚨 dispatched {:,} but received {:,} ({} units short, {:.2f}% deviation — FLAGGED)".format(
                dispatched, received_qty or 0, missing, qty_dev)
        )
    elif qty_status == "PENDING":
        notes_parts.append("Qty — awaiting receiver confirmation")

    if expiry_status == "MATCH":
        notes_parts.append("Expiry ✓ matches batch record")
    elif expiry_status == "MISMATCH":
        notes_parts.append(
            f"Expiry ⚠ batch says {batch.expiry_date.date() if batch.expiry_date else '?'}, "
            f"received says {received_expiry.date() if received_expiry else '?'}"
        )
    elif expiry_status == "PENDING":
        notes_parts.append("Expiry — awaiting confirmation")

    return LegReport(
        leg=leg_name,
        shipment_code=shipment.shipment_code or shipment.id[:8],
        from_party=from_party,
        to_party=to_party,
        medicine_name=batch.name,
        batch_number=batch.batch_number,
        dispatched_qty=dispatched,
        received_qty=received_qty,
        batch_expiry=batch.expiry_date,
        received_expiry=received_expiry,
        declared_temp=batch.storage_temp_declared,
        received_temp=received_temp,
        qty_status=qty_status,
        expiry_status=expiry_status,
        temp_status=temp_status,
        qty_deviation_pct=qty_dev,
        temp_deviation_c=temp_dev,
        notes=" | ".join(notes_parts),
    )
