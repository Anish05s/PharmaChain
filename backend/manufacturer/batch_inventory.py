"""Helpers for partial batch dispatch tracking."""
from sqlalchemy.orm import Session
from models import Shipment, MedicineBatch


def dispatched_units_for_batch(
    db: Session, batch: MedicineBatch, manufacturer_id: str
) -> int:
    shipments = (
        db.query(Shipment)
        .filter(
            Shipment.batch_id == batch.id,
            Shipment.from_entity_id == manufacturer_id,
        )
        .all()
    )
    total = 0
    for shipment in shipments:
        if shipment.quantity_dispatched is not None:
            total += shipment.quantity_dispatched
        else:
            # Legacy rows created before partial dispatch
            total += batch.quantity
    return total


def remaining_units_for_batch(
    db: Session, batch: MedicineBatch, manufacturer_id: str
) -> int:
    return max(0, batch.quantity - dispatched_units_for_batch(db, batch, manufacturer_id))
