"""
Inventory AI — Stock threshold monitor (MVP).
Communicates with other modules ONLY via the database.

Runs every POLL_INTERVAL_MINUTES via APScheduler on FastAPI startup.
When stock < reorder_threshold:
  - Creates a RestockRequest (status=pending)
  - Creates a Notification for the relevant user
  - Supplier:  auto-request to manufacturer
  - Consumer:  auto-request to supplier
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from models import StockLevel, RestockRequest, Notification, User

logger = logging.getLogger(__name__)

POLL_INTERVAL_MINUTES = 5


def check_stock_levels(db: Session) -> int:
    """
    Scan all stock_levels. For each entry below reorder_threshold,
    create a RestockRequest (if one doesn't already exist in 'pending' state)
    and a Notification.

    Returns the count of new alerts created.
    """
    alerts_created = 0

    try:
        low_stock_rows = (
            db.query(StockLevel)
            .filter(StockLevel.quantity < StockLevel.reorder_threshold)
            .all()
        )

        for row in low_stock_rows:
            # Deduplicate: skip if a pending request already exists
            existing = (
                db.query(RestockRequest)
                .filter(
                    RestockRequest.requester_entity_id == row.entity_id,
                    RestockRequest.medicine_name == row.medicine_name,
                    RestockRequest.status == "pending",
                )
                .first()
            )
            if existing:
                continue

            urgency = _urgency_level(row.quantity, row.reorder_threshold)

            restock = RestockRequest(
                requester_entity_id=row.entity_id,
                requester_type=row.entity_type,
                target_entity_id=None,   # matched by supplier/manufacturer in their dashboards
                medicine_name=row.medicine_name,
                quantity_requested=row.reorder_threshold * 2,  # request 2x threshold
                reason=(
                    f"AI auto-alert: stock {row.quantity} units is below "
                    f"reorder threshold {row.reorder_threshold} units."
                ),
                urgency=urgency,
                status="pending",
            )
            db.add(restock)

            # Find users linked to this entity for notification
            users = (
                db.query(User)
                .filter(User.entity_id == row.entity_id)
                .all()
            )
            for user in users:
                notif = Notification(
                    recipient_id=user.id,
                    type="stock_alert",
                    title=f"⚠️ Low Stock: {row.medicine_name}",
                    message=(
                        f"Stock level for {row.medicine_name} is {row.quantity} units "
                        f"(threshold: {row.reorder_threshold}). "
                        f"An emergency restock request has been auto-generated. "
                        f"Urgency: {urgency.upper()}."
                    ),
                    read=False,
                )
                db.add(notif)

            alerts_created += 1
            logger.info(
                "InventoryAI: low stock alert — entity=%s medicine=%s qty=%d threshold=%d urgency=%s",
                row.entity_id, row.medicine_name, row.quantity, row.reorder_threshold, urgency,
            )

        if alerts_created:
            db.commit()

    except Exception as exc:
        logger.error("InventoryAI: check_stock_levels failed: %s", exc)
        db.rollback()

    return alerts_created


def _urgency_level(quantity: int, threshold: int) -> str:
    """Return urgency string based on how far below threshold stock is."""
    if threshold == 0:
        return "normal"
    ratio = quantity / threshold
    if ratio <= 0.25:
        return "critical"
    elif ratio <= 0.50:
        return "high"
    else:
        return "normal"


def start_scheduler(db_session_factory) -> Optional[object]:
    """
    Start APScheduler background scheduler.
    db_session_factory: callable that returns a new SQLAlchemy Session.
    Returns the scheduler instance (or None if APScheduler is not installed).
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning(
            "APScheduler not installed — stock threshold monitoring disabled. "
            "Run: pip install apscheduler"
        )
        return None

    def _job():
        db = db_session_factory()
        try:
            n = check_stock_levels(db)
            if n:
                logger.info("InventoryAI scheduler: created %d alerts", n)
        finally:
            db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _job,
        trigger="interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="inventory_ai_stock_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "InventoryAI scheduler started — polling every %d minutes.",
        POLL_INTERVAL_MINUTES,
    )
    return scheduler
