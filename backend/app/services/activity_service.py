"""
Activity feed service — KRAFZEN AI
Owner: Tazwar

Records export lifecycle events for the activity feed.
Payload shape finalized with Sunny (Week 2):
  - message: human-readable string rendered as feed main line
  - metadata: {project_name, status, format (nice-to-have), source}
  - actor: {display_name, avatar_url} joined inline
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.utils.logger import logger


async def record_event(
    event_name: str,         # e.g. "export.completed"
    job_id: str,
    project_id: str,
    actor_user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any] | None:
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
        "created_at": datetime.now(UTC).isoformat(),
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


async def record_workspace_event(
    *,
    event_name: str,
    workspace_id: str,
    actor_user_id: str,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Persist a workspace audit event, failing explicitly if it cannot be stored."""
    if not event_name or not event_name.strip():
        raise ValueError("An audit event name is required")
    if not workspace_id:
        raise ValueError("A workspace_id is required")
    if not actor_user_id:
        raise ValueError("An authenticated actor_user_id is required")

    payload = {
        "event_name": event_name,
        "workspace_id": workspace_id,
        "actor_user_id": actor_user_id,
        "message": message or _default_message(event_name),
        "metadata": metadata or {},
        "created_at": datetime.now(UTC).isoformat(),
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            logger.info(
                "[activity_service] Workspace event recorded",
                event_name=event_name,
                workspace_id=workspace_id,
            )
            return response.data[0]
        raise RuntimeError("Workspace audit event insert returned no data")
    except Exception as e:
        logger.error(
            "[activity_service] Failed to record workspace event",
            event_name=event_name,
            workspace_id=workspace_id,
            error=str(e),
            exc_info=True,
        )
        raise


async def record_file_event(
    *,
    event_name: str,
    file_id: str,
    project_id: str,
    job_id: str,
    actor_user_id: str,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Append an activity event tied to a file and its authenticated actor."""
    if not event_name or not event_name.strip():
        raise ValueError("An activity event name is required")
    if not file_id or not project_id or not job_id or not actor_user_id:
        raise ValueError("File, project, job, and authenticated actor IDs are required")

    payload = {
        "event_name": event_name,
        "file_id": file_id,
        "project_id": project_id,
        "job_id": job_id,
        "actor_user_id": actor_user_id,
        "message": message or _default_message(event_name),
        "metadata": metadata or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            return response.data[0]
        raise RuntimeError("File activity event insert returned no data")
    except Exception as e:
        logger.error(
            "[activity_service] Failed to record file event",
            event_name=event_name,
            file_id=file_id,
            error=str(e),
            exc_info=True,
        )
        raise


async def get_file_activity(
    file_id: str,
    job_id: str,
    project_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return events attached to a file plus its job's lifecycle events."""
    try:
        responses = await asyncio.gather(
            run_in_threadpool(
                lambda: db.table("activity_events").select("*, profiles(display_name, avatar_url)")
                    .eq("file_id", file_id)
                    .eq("project_id", project_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
            ),
            run_in_threadpool(
                lambda: db.table("activity_events").select("*, profiles(display_name, avatar_url)")
                    .eq("job_id", job_id)
                    .eq("project_id", project_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
            ),
        )
        rows = {
            str(row.get("id") or row.get("event_id")): row
            for response in responses
            for row in (response.data or [])
            if not row.get("file_id") or str(row["file_id"]) == file_id
        }
        ordered = sorted(
            rows.values(),
            key=lambda row: row.get("created_at") or row.get("timestamp") or "",
            reverse=True,
        )
        return [_shape_activity_row(row) for row in ordered[:limit]]
    except Exception as e:
        logger.error(
            "[activity_service] Failed to fetch file activity",
            file_id=file_id,
            error=str(e),
            exc_info=True,
        )
        raise


async def get_project_activity(
    project_id: str,
    user_id: str,          # required — Yehor confirmed service role bypasses RLS
    limit: int = 50,
) -> list[dict[str, Any]]:
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


async def get_workspace_activity(workspace_id: str, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch only events assigned to this workspace for an owner or current member."""
    try:
        workspace_res = await run_in_threadpool(
            lambda: db.table("workspaces").select("owner_id")
                .eq("id", workspace_id).maybe_single().execute()
        )
        if not workspace_res or not workspace_res.data:
            logger.warning("[activity_service] Workspace not found", workspace_id=workspace_id)
            return []

        is_member = await run_in_threadpool(
            lambda: db.table("workspace_members").select("user_id")
                .eq("workspace_id", workspace_id).eq("user_id", user_id)
                .maybe_single().execute()
        )
        is_owner = workspace_res.data["owner_id"] == user_id
        if not is_owner and (not is_member or not is_member.data):
            logger.warning("[activity_service] Not a workspace member", workspace_id=workspace_id, user_id=user_id[:8])
            return []

        response = await run_in_threadpool(
            lambda: db.table("activity_events").select("*, profiles(display_name, avatar_url)")
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True).limit(limit).execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except Exception as e:
        logger.error("[activity_service] Failed to fetch workspace activity", workspace_id=workspace_id, error=str(e), exc_info=True)
        return []


def _shape_activity_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten actor profile into the row for Sunny's frontend.
    Returns: event_name, message, created_at, actor {display_name, avatar_url}, metadata.
    """
    shaped = dict(row)
    profile = shaped.get("profiles")
    if isinstance(profile, list):
        profile = profile[0] if profile else None
    profile = profile if isinstance(profile, dict) else {}
    shaped["actor"] = {
        "user_id": shaped.get("actor_user_id"),
        "display_name": profile.get("display_name"),
        "avatar_url": profile.get("avatar_url"),
    }
    return shaped


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