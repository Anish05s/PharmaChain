"""Notification Service — FastAPI router"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from auth.dependencies import get_current_user
from models import User
from notification_service.service import (
    list_notifications,
    get_unread_count,
    mark_read,
    mark_all_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationItem(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int


@router.get("", response_model=List[NotificationItem])
def get_notifications(
    unread_only: bool = False,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the logged-in user."""
    return list_notifications(db, current_user.id, limit=limit, unread_only=unread_only)


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return unread notification count (used by the header bell)."""
    return {"count": get_unread_count(db, current_user.id)}


@router.post("/{notification_id}/read", response_model=NotificationItem)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read."""
    notif = mark_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notif


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications read for the current user."""
    count = mark_all_read(db, current_user.id)
    return {"marked_read": count}
