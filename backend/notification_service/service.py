"""
Notification Service
====================
Provides helpers to create and read in-app notifications.
Writes to the `notifications` DB table.

Redis integration: graceful — if Redis is unavailable, falls back to
DB polling on the frontend. No code change required in either case.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from models import Notification

logger = logging.getLogger(__name__)


# ── Redis client (optional) ──────────────────────────────────────────────────
_redis_client = None


def init_redis(redis_url: str) -> None:
    """
    Attempt to connect to Redis. Called at startup.
    Falls back silently if Redis is unreachable.
    """
    global _redis_client
    try:
        import redis as redis_lib
        client = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        logger.info("NotificationService: Redis connected at %s", redis_url)
    except Exception as exc:
        logger.warning(
            "NotificationService: Redis unavailable (%s). "
            "Real-time delivery disabled — using DB polling fallback.",
            exc,
        )
        _redis_client = None


# ── Core helpers ─────────────────────────────────────────────────────────────

def create_notification(
    db: Session,
    recipient_id: str,
    notif_type: str,
    title: str,
    message: str,
) -> Notification:
    """
    Write a notification to the DB.
    Also publishes to Redis channel 'notifications:{recipient_id}' if available.
    """
    notif = Notification(
        recipient_id=recipient_id,
        type=notif_type,
        title=title,
        message=message,
        read=False,
    )
    db.add(notif)
    db.flush()  # get the ID without full commit

    # Redis pub/sub — best effort
    if _redis_client:
        try:
            import json
            _redis_client.publish(
                f"notifications:{recipient_id}",
                json.dumps({"id": notif.id, "title": title, "type": notif_type}),
            )
        except Exception as exc:
            logger.debug("Redis publish failed (non-fatal): %s", exc)

    return notif


def get_unread_count(db: Session, user_id: str) -> int:
    """Count unread notifications for a user."""
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_id == user_id,
            Notification.read == False,  # noqa: E712
        )
        .count()
    )


def list_notifications(
    db: Session,
    user_id: str,
    limit: int = 30,
    unread_only: bool = False,
) -> List[Notification]:
    """Fetch notifications for a user, newest first."""
    q = db.query(Notification).filter(Notification.recipient_id == user_id)
    if unread_only:
        q = q.filter(Notification.read == False)  # noqa: E712
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


def mark_read(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
    """Mark a single notification as read. Returns the updated row or None."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
        )
        .first()
    )
    if notif:
        notif.read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, user_id: str) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    updated = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == user_id,
            Notification.read == False,  # noqa: E712
        )
        .update({"read": True})
    )
    db.commit()
    return updated
