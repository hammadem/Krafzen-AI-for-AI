"""
Notification service — KRAFZEN AI
Owner: Tazwar

In-app notification delivery for export lifecycle events.
Table: notifications (see migration 004_week2_activity_notifications.sql)
Coordinate with Sunny: she reads GET /notifications and unread count.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.utils.logger import logger

VALID_NOTIFICATION_TYPES = {
    "export_completed",
    "export_failed",
    "export_requires_review",
    "validation_update",
}


async def create_notification(
    user_id: str,
    notification_type: str,
    message: str,
    job_id: str | None = None,
    project_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Insert a new unread notification for a user.
    """
    if notification_type not in VALID_NOTIFICATION_TYPES:
        logger.warning("[notification_service] Unknown notification type", type=notification_type)

    payload = {
        "user_id": user_id,
        "type": notification_type,
        "message": message,
        "job_id": job_id,
        "project_id": project_id,
        "metadata": metadata or {},
        "is_read": False,
        "created_at": datetime.now(UTC).isoformat(),
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("notifications").insert(payload).execute()
        )
        if response and response.data:
            logger.info("[notification_service] Notification created", type=notification_type, user_id=user_id[:8])
            return response.data[0]
        return None
    except Exception as e:
        logger.error("[notification_service] Insert failed", error=str(e), exc_info=True)
        return None


async def get_notifications(user_id: str, unread_only: bool = False) -> list:
    try:
        query = db.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True)
        if unread_only:
            query = query.eq("is_read", False)
        response = await run_in_threadpool(lambda: query.execute())
        return response.data if response and response.data else []
    except Exception as e:
        logger.error("[notification_service] Fetch failed", error=str(e), exc_info=True)
        return []


async def mark_as_read(notification_id: str, user_id: str) -> bool:
    try:
        response = await run_in_threadpool(
            lambda: db.table("notifications")
                .update({"is_read": True})
                .eq("id", notification_id)
                .eq("user_id", user_id)  # ownership guard
                .execute()
        )
        return bool(response and response.data)
    except Exception as e:
        logger.error("[notification_service] Mark-read failed", error=str(e), exc_info=True)
        return False