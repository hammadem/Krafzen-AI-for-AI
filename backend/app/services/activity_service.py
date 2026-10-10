"""
Activity feed service — KRAFZEN AI
Owner: Tazwar

Records append-only audit events and returns the canonical audit contract alongside
legacy activity-feed aliases.
Legacy payload shape finalized with Sunny (Week 2):
  - message: human-readable string rendered as feed main line
  - metadata: {project_name, status, format (nice-to-have), source}
  - actor: {display_name, avatar_url} joined inline
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger


async def record_event(
    event_name: Optional[str] = None,
    job_id: Optional[str] = None,
    project_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    *,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Append one audit event. The old event_name/job_id arguments remain supported
    while callers migrate to action/entity_type/entity_id.
    """
    resolved_action = action or event_name
    if not resolved_action:
        raise ValueError("An audit event action is required")

    event_metadata = metadata or {}
    resolved_entity_type = entity_type or _entity_type_for(
        resolved_action, job_id=job_id, project_id=project_id
    )
    resolved_entity_id = entity_id or _metadata_entity_id(resolved_action, event_metadata)
    if resolved_entity_id is None:
        if resolved_entity_type == "export_job":
            resolved_entity_id = job_id
        elif resolved_entity_type == "project":
            resolved_entity_id = project_id
        elif resolved_entity_type == "legacy_event":
            resolved_entity_id = job_id or project_id
    if not resolved_entity_id:
        raise ValueError("An audit event entity_id is required")

    event_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    legacy_job_id = job_id
    if legacy_job_id is None and resolved_entity_type == "export_job":
        legacy_job_id = resolved_entity_id

    payload = {
        "event_id": event_id,
        "id": event_id,
        "action": resolved_action,
        "event_name": resolved_action,
        "entity_type": resolved_entity_type,
        "entity_id": resolved_entity_id,
        "organization_id": organization_id,
        "timestamp": timestamp,
        "created_at": timestamp,
        "job_id": legacy_job_id,
        "project_id": project_id,
        "actor_user_id": actor_user_id,
        "message": message or _default_message(resolved_action),
        "metadata": event_metadata,
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            logger.info(
                "[activity_service] Event recorded",
                action=resolved_action,
                entity_id=resolved_entity_id,
            )
            return _shape_activity_row(response.data[0])
        raise RuntimeError("Activity event insert returned no data")
    except Exception as e:
        logger.error(
            "[activity_service] Failed to record event",
            action=resolved_action,
            entity_id=resolved_entity_id,
            error=str(e),
            exc_info=True,
        )
        raise


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

        # Keep returning legacy aliases as well as canonical audit fields.
        response = await run_in_threadpool(
            lambda: db.table("activity_events")
                .select("*")
                .eq("project_id", project_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except Exception as e:
        logger.error("[activity_service] Failed to fetch activity", project_id=project_id, error=str(e), exc_info=True)
        return []


async def get_workspace_activity(workspace_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch only events assigned to this workspace for a verified member."""
    try:
        is_member = await run_in_threadpool(
            lambda: db.table("workspace_members").select("user_id")
                .eq("workspace_id", workspace_id).eq("user_id", user_id)
                .maybe_single().execute()
        )
        if not is_member or not is_member.data:
            logger.warning("[activity_service] Not a workspace member", workspace_id=workspace_id, user_id=user_id[:8])
            return []

        response = await run_in_threadpool(
            lambda: db.table("activity_events").select("*, profiles(display_name, avatar_url)")
                .eq("organization_id", workspace_id)
                .order("timestamp", desc=True).limit(limit).execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except Exception as e:
        logger.error("[activity_service] Failed to fetch workspace activity", workspace_id=workspace_id, error=str(e), exc_info=True)
        return []


def _shape_activity_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return canonical audit fields and legacy aliases for existing feed clients.
    """
    shaped = dict(row)
    action = shaped.get("action") or shaped.get("event_name")
    entity_type = shaped.get("entity_type") or _entity_type_for(
        action or "", job_id=shaped.get("job_id"), project_id=shaped.get("project_id")
    )
    entity_id = shaped.get("entity_id") or shaped.get("job_id") or shaped.get("project_id")
    event_id = shaped.get("event_id") or shaped.get("id")
    timestamp = shaped.get("timestamp") or shaped.get("created_at")

    shaped.update({
        "event_id": event_id,
        "id": shaped.get("id") or event_id,
        "organization_id": shaped.get("organization_id"),
        "action": action,
        "event_name": shaped.get("event_name") or action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timestamp": timestamp,
        "created_at": shaped.get("created_at") or timestamp,
        "metadata": shaped.get("metadata") or {},
    })

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


def _entity_type_for(
    action: str,
    *,
    job_id: Optional[str],
    project_id: Optional[str],
) -> str:
    if action.startswith("file."):
        return "file"
    if action.startswith("ai.review_"):
        return "ai_review"
    if action.startswith("ai.generation_"):
        return "ai_generation"
    if action.startswith("ai.suggestion_"):
        return "ai_suggestion"
    if action.startswith("revision."):
        return "revision"
    if action.startswith("member."):
        return "member"
    if action == "permission.changed":
        return "permission"
    if action.startswith("export."):
        return "export_job"
    if job_id:
        return "export_job"
    if project_id:
        return "project"
    return "legacy_event"


def _metadata_entity_id(action: str, metadata: Dict[str, Any]) -> Optional[str]:
    generic_id = metadata.get("entity_id")
    if generic_id:
        return str(generic_id)

    reference_key = {
        "file.": "file_id",
        "ai.review_": "review_id",
        "ai.generation_": "generation_id",
        "ai.suggestion_": "suggestion_id",
        "revision.": "revision_id",
        "member.": "member_id",
        "permission.changed": "permission_id",
    }
    for prefix, key in reference_key.items():
        if action == prefix or action.startswith(prefix):
            value = metadata.get(key)
            return str(value) if value else None
    return None


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