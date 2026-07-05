"""
Activity feed service — KRAFZEN AI
Owner: Tazwar

Records export lifecycle events for the activity feed.
Payload shape finalized with Sunny (Week 2):
  - message: human-readable string rendered as feed main line
  - metadata: {project_name, status, format (nice-to-have), source}
  - actor: {display_name, avatar_url} joined inline
"""

from typing import Any, Dict, List, Optional
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
    message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Insert a single activity record.
    message: human-readable string for Sunny's feed main line.
    metadata should include: project_name, status, format (optional), source.
    """
    payload = {
        "event_name": event_name,
        "job_id": job_id,
        "project_id": project_id,
        "actor_user_id": actor_user_id,
        "message": message or _default_message(event_name),
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            logger.info("[activity_service] Event recorded", event_name=event_name, job_id=job_id)
            return response.data[0]
        logger.warning("[activity_service] Insert returned no data", event_name=event_name)
        return None
    except Exception as e:
        logger.error("[activity_service] Failed to record event", event_name=event_name, error=str(e), exc_info=True)
        return None


async def get_project_activity(
    project_id: str,
    user_id: str,          # required — Yehor confirmed service role bypasses RLS
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch recent activity for a project with actor info joined inline.
    Explicit ownership check required (service role client bypasses RLS).
    Sunny's feed expects: event_name, message, created_at, actor.display_name, actor.avatar_url.
    """
    try:
        # Ownership check — same pattern as job_queries._user_owns_project
        owns = await run_in_threadpool(
            lambda: db.table("projects")
                .select("id")
                .eq("id", project_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
        )
        if not owns or not owns.data:
            logger.warning("[activity_service] Ownership check failed", project_id=project_id, user_id=user_id[:8])
            return []

        # Fetch events with actor profile joined
        response = await run_in_threadpool(
            lambda: db.table("activity_events")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except Exception as e:
        logger.error("[activity_service] Failed to fetch activity", project_id=project_id, error=str(e), exc_info=True)
        return []


async def get_workspace_activity(workspace_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """v1 rollup via membership proxy (no projects.workspace_id yet, per Kiruthika).
    Caveat: a member's activity on projects unrelated to this workspace can leak
    in until projects.workspace_id lands — acceptable for dashboard v1, not exact."""
    try:
        is_member = await run_in_threadpool(
            lambda: db.table("workspace_members").select("user_id")
                .eq("workspace_id", workspace_id).eq("user_id", user_id)
                .maybe_single().execute()
        )
        if not is_member or not is_member.data:
            logger.warning("[activity_service] Not a workspace member", workspace_id=workspace_id, user_id=user_id[:8])
            return []

        members_res = await run_in_threadpool(
            lambda: db.table("workspace_members").select("user_id").eq("workspace_id", workspace_id).execute()
        )
        member_ids = [m["user_id"] for m in (members_res.data or [])]
        if not member_ids:
            return []

        response = await run_in_threadpool(
            lambda: db.table("activity_events").select("*, profiles(display_name, avatar_url)")
                .in_("actor_user_id", member_ids).order("created_at", desc=True).limit(limit).execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except Exception as e:
        logger.error("[activity_service] Failed to fetch workspace activity", workspace_id=workspace_id, error=str(e), exc_info=True)
        return []


def _shape_activity_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten actor profile into the row for Sunny's frontend.
    Returns: event_name, message, created_at, actor {display_name, avatar_url}, metadata.
    """
    row["actor"] = {
        "user_id": row.get("actor_user_id"),
        "display_name": None,  # default to None if not found
        "avatar_url": None,
    }
    return row


def _default_message(event_name: str) -> str:
    """Fallback human-readable message when caller doesn't supply one."""
    return {
        "export.queued": "Export queued",
        "export.processing": "Export started",
        "export.validating": "Validating export",
        "export.completed": "Export completed",
        "export.failed": "Export failed",
        "export.requires_review": "Export needs manual review",
    }.get(event_name, event_name)