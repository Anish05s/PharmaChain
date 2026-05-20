"""notification_service package"""
from notification_service.service import (
    create_notification,
    get_unread_count,
    list_notifications,
    mark_read,
    mark_all_read,
    init_redis,
)

__all__ = [
    "create_notification",
    "get_unread_count",
    "list_notifications",
    "mark_read",
    "mark_all_read",
    "init_redis",
]
