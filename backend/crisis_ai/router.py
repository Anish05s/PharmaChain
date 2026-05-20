"""Crisis AI — FastAPI router"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth.dependencies import get_current_user
from models import DisruptionEvent, User
from crisis_ai.rules import get_recommendations, supported_event_types

router = APIRouter(prefix="/crisis", tags=["Crisis AI"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class DisruptionEventCreate(BaseModel):
    event_type: str
    region: str
    severity: str = "medium"   # low | medium | high | critical
    source: str = "manual"
    affected_routes: Optional[str] = None


class DisruptionEventResponse(BaseModel):
    id: str
    event_type: str
    region: str
    severity: str
    source: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    affected_routes: Optional[str]

    class Config:
        from_attributes = True


class MedicineRecommendation(BaseModel):
    medicine: str
    rationale: str
    quantity_multiplier: float


class CrisisRecommendationResponse(BaseModel):
    event_id: str
    event_type: str
    region: str
    severity: str
    recommendations: List[MedicineRecommendation]
    supported_event_types: List[str]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/events", response_model=DisruptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_disruption_event(
    data: DisruptionEventCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Manually submit a disruption event (flood, earthquake, outbreak, etc.)."""
    valid_types = supported_event_types()
    if data.event_type.lower() not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported event_type. Supported: {valid_types}",
        )

    valid_severities = {"low", "medium", "high", "critical"}
    if data.severity.lower() not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"severity must be one of: {valid_severities}",
        )

    event = DisruptionEvent(
        event_type=data.event_type.lower(),
        region=data.region,
        severity=data.severity.lower(),
        source=data.source,
        affected_routes=data.affected_routes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/events", response_model=List[DisruptionEventResponse])
def list_disruption_events(
    active_only: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List disruption events. By default returns only unresolved (active) events."""
    q = db.query(DisruptionEvent)
    if active_only:
        q = q.filter(DisruptionEvent.resolved_at == None)  # noqa: E711
    return q.order_by(DisruptionEvent.detected_at.desc()).limit(limit).all()


@router.patch("/events/{event_id}/resolve", response_model=DisruptionEventResponse)
def resolve_disruption_event(
    event_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Mark a disruption event as resolved."""
    event = db.query(DisruptionEvent).filter(DisruptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event


@router.get("/recommendations/{event_id}", response_model=CrisisRecommendationResponse)
def get_crisis_recommendations(
    event_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Get AI-generated medicine recommendations for a specific disruption event.
    Returns a list of medicines to pre-position, with quantity multipliers.
    """
    event = db.query(DisruptionEvent).filter(DisruptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Disruption event not found")

    recommendations = get_recommendations(event.event_type, event.severity)

    return CrisisRecommendationResponse(
        event_id=event.id,
        event_type=event.event_type,
        region=event.region,
        severity=event.severity,
        recommendations=recommendations,
        supported_event_types=supported_event_types(),
    )


@router.get("/event-types")
def list_event_types(_user: User = Depends(get_current_user)):
    """Return list of supported event types."""
    return {"event_types": supported_event_types()}
