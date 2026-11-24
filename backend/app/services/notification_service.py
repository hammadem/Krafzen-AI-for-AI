"""
Notification service — KRAFZEN AI
Owner: Tazwar

In-app notification delivery for export lifecycle events.
Table: notifications (see migration 004_week2_activity_notifications.sql)
Coordinate with Sunny: she reads GET /notifications and unread count.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.supabase_client import db
from app.utils.logger import logger

VALID_NOTIFICATION_TYPES = {
    "export_completed",
    "export_failed",
    "export_requires_review",
    "validation_update",
    "import_completed",
    "project_assignment",
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
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as e:
        logger.error("[notification_service] Insert failed", error=str(e), exc_info=True)
        return None


async def get_notification_page(
    user_id: str, unread_only: bool = False, limit: int = 20, offset: int = 0
) -> tuple[list[dict[str, Any]], int]:
    """Read persisted notifications only, with an authenticated ownership filter."""
    if not 1 <= limit <= 100 or not 0 <= offset <= 10000:
        raise HTTPException(status_code=422, detail="Invalid notification pagination")
    try:
        def fetch():
            query = db.table("notifications").select("*", count="exact").eq("user_id", user_id)
            if unread_only:
                query = query.eq("is_read", False)
            return query.order("created_at", desc=True).order("id", desc=True).range(offset, offset + limit - 1).execute()
        response = await run_in_threadpool(fetch)
        if response is None or response.count is None:
            raise HTTPException(status_code=503, detail="Notification history unavailable")
        return response.data or [], response.count
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        logger.error("[notification_service] Fetch failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=503, detail="Notification history unavailable") from exc


async def get_notifications(user_id: str, unread_only: bool = False) -> list:
    rows, _ = await get_notification_page(user_id, unread_only, limit=100)
    return rows


async def mark_as_read(notification_id: str, user_id: str) -> bool:
    try:
        response = await run_in_threadpool(
            lambda: db.table("notifications")
                .update({"is_read": True})
                .eq("id", notification_id)
                .eq("user_id", user_id)
                .execute()
        )
        if response is None:
            raise HTTPException(status_code=503, detail="Notification update unavailable")
        return bool(response.data)
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        logger.error("[notification_service] Mark-read failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=503, detail="Notification update unavailable") from exc
