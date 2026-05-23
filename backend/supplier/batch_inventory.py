"""Partial dispatch tracking for supplier warehouse (per batch)."""
from sqlalchemy.orm import Session
from models import Shipment, MedicineBatch, HandoffRecord


def _shipment_units(shipment: Shipment, batch: MedicineBatch, db: Session, stage: str) -> int:
    # First, always trust the receiving party's reported quantity for their own inventory
    handoff = (
        db.query(HandoffRecord)
        .filter(
            HandoffRecord.shipment_id == shipment.id,
            HandoffRecord.stage == stage,
        )
        .first()
    )
    if handoff and handoff.quantity_reported is not None:
        return handoff.quantity_reported

    # Fallback to what was dispatched
    if shipment.quantity_dispatched is not None:
        return shipment.quantity_dispatched
        
    # Final fallback to batch size
    return batch.quantity


def received_units_for_batch(
    db: Session, batch: MedicineBatch, supplier_id: str
) -> int:
    incoming = (
        db.query(Shipment)
        .filter(
            Shipment.batch_id == batch.id,
            Shipment.to_entity_id == supplier_id,
            Shipment.status == "delivered",
        )
        .all()
    )
    return sum(_shipment_units(s, batch, db, "supplier_receipt") for s in incoming)


def outbound_dispatched_for_batch(
    db: Session, batch: MedicineBatch, supplier_id: str
) -> int:
    outbound = (
        db.query(Shipment)
        .filter(
            Shipment.batch_id == batch.id,
            Shipment.from_entity_id == supplier_id,
        )
        .all()
    )
    total = 0
    for shipment in outbound:
        if shipment.quantity_dispatched is not None:
            total += shipment.quantity_dispatched
        else:
            total += batch.quantity
    return total


def remaining_units_for_batch(
    db: Session, batch: MedicineBatch, supplier_id: str
) -> int:
    return max(
        0,
        received_units_for_batch(db, batch, supplier_id)
        - outbound_dispatched_for_batch(db, batch, supplier_id),
    )
