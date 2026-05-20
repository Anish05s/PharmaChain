"""Emergency stock / restock request notifications for portal header bars."""
from typing import List
from sqlalchemy.orm import Session
from models import RestockRequest, Manufacturer, Supplier, Consumer

URGENCY_ORDER = {"critical": 0, "high": 1, "normal": 2}


def _target_name(db: Session, target_entity_id: str) -> str:
    for model in (Manufacturer, Supplier, Consumer):
        row = db.query(model).filter(model.id == target_entity_id).first()
        if row:
            return row.name
    return target_entity_id or "Unknown"


def _requester_name(db: Session, requester_type: str, requester_entity_id: str) -> str:
    if requester_type == "supplier":
        row = db.query(Supplier).filter(Supplier.id == requester_entity_id).first()
        return row.name if row else requester_entity_id
    if requester_type == "consumer":
        row = db.query(Consumer).filter(Consumer.id == requester_entity_id).first()
        return row.name if row else requester_entity_id
    if requester_type == "manufacturer":
        row = db.query(Manufacturer).filter(Manufacturer.id == requester_entity_id).first()
        return row.name if row else requester_entity_id
    return requester_entity_id or "Unknown"


def _sort_requests(requests: List[RestockRequest]) -> List[RestockRequest]:
    return sorted(
        requests,
        key=lambda r: (
            URGENCY_ORDER.get((r.urgency or "normal").lower(), 9),
            -(r.created_at.timestamp() if r.created_at else 0),
        ),
    )


def notifications_for_manufacturer(db: Session, manufacturer_id: str) -> List[RestockRequest]:
    """Supplier restock requests to this manufacturer + all pending hospital requests."""
    to_manufacturer = (
        db.query(RestockRequest)
        .filter(
            RestockRequest.target_entity_id == manufacturer_id,
            RestockRequest.status == "pending",
        )
        .all()
    )
    from_hospitals = (
        db.query(RestockRequest)
        .filter(
            RestockRequest.requester_type == "consumer",
            RestockRequest.status == "pending",
        )
        .all()
    )
    seen = set()
    merged: List[RestockRequest] = []
    for req in to_manufacturer + from_hospitals:
        if req.id in seen:
            continue
        seen.add(req.id)
        merged.append(req)
    return _sort_requests(merged)


def to_notification_items(db: Session, requests: List[RestockRequest]):
    from shared.schemas import EmergencyNotificationItem

    return [
        EmergencyNotificationItem(
            id=req.id,
            requester_type=req.requester_type or "unknown",
            requester_name=_requester_name(db, req.requester_type, req.requester_entity_id),
            target_entity_id=req.target_entity_id,
            target_name=_target_name(db, req.target_entity_id),
            medicine_name=req.medicine_name,
            quantity_requested=req.quantity_requested,
            reason=req.reason or "",
            urgency=req.urgency or "normal",
            status=req.status,
            created_at=req.created_at,
        )
        for req in requests
    ]


def notifications_for_supplier(db: Session, supplier_id: str) -> List[RestockRequest]:
    return _sort_requests(
        db.query(RestockRequest)
        .filter(
            RestockRequest.target_entity_id == supplier_id,
            RestockRequest.requester_type == "consumer",
            RestockRequest.status == "pending",
        )
        .all()
    )
