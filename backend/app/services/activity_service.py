"""
Activity feed service — KRAFZEN AI
Owner: Tazwar

Records export lifecycle events for the activity feed.
Coordinate with Sunny on payload structure before finalizing.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger


async def record_event(
    event_name: str,         # e.g. "export.completed"
    job_id: str,
    project_id: str,
    actor_user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Insert a single activity record.
    event_name must be in the export.* namespace per event taxonomy.
    """
    payload = {
        "event_name": event_name,
        "job_id": job_id,
        "project_id": project_id,
        "actor_user_id": actor_user_id,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            logger.info("[activity_service] Event recorded", event=event_name, job_id=job_id)
            return response.data[0]
        logger.warning("[activity_service] Insert returned no data", event=event_name)
        return None
    except Exception as e:
        logger.error("[activity_service] Failed to record event", event=event_name, error=str(e), exc_info=True)
        return None


async def get_project_activity(
    project_id: str,
    limit: int = 50,
) -> list:
    """
    Fetch recent activity for a project, most recent first.
    Used by Sunny's frontend activity feed — coordinate payload shape with him.
    """
    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
        )
        return response.data if response and response.data else []
    except Exception as e:
        logger.error("[activity_service] Failed to fetch activity", project_id=project_id, error=str(e), exc_info=True)
        return []