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

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.supabase_client import db
from app.utils.logger import logger


def _bounded_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("Activity limit must be a positive integer")
    return min(limit, 100)


def _activity_sort_key(row: dict[str, Any]) -> tuple[float, str]:
    value = row.get("timestamp") or row.get("created_at")
    try:
        raw_time = str(value)
        if raw_time.endswith("Z"):
            raw_time = f"{raw_time[:-1]}+00:00"
        event_time = datetime.fromisoformat(raw_time)
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=UTC)
        timestamp = event_time.timestamp()
    except (TypeError, ValueError, OverflowError):
        timestamp = float("-inf")
    return timestamp, str(row.get("event_id") or row.get("id") or "")


async def record_event(
    event_name: str | None = None,
    job_id: str | None = None,
    project_id: str | None = None,
    actor_user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
    *,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    file_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """
    Backward-compatible activity writer. New callers should use
    record_audit_event with explicit entity fields.
    """
    resolved_action = action or event_name
    if not resolved_action:
        raise ValueError("An audit event action is required")

    event_metadata = metadata or {}
    resolved_entity_type = entity_type or _entity_type_for(
        resolved_action, job_id=job_id, project_id=project_id
    )
    resolved_entity_id = (
        entity_id
        or file_id
        or _metadata_entity_id(resolved_action, event_metadata)
    )
    if resolved_entity_id is None:
        if resolved_entity_type == "export_job":
            resolved_entity_id = job_id
        elif resolved_entity_type == "project":
            resolved_entity_id = project_id
        elif resolved_entity_type == "legacy_event":
            resolved_entity_id = job_id or project_id
    if not resolved_entity_id:
        raise ValueError("An audit event entity_id is required")

    return await record_audit_event(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        project_id=project_id,
        action=resolved_action,
        entity_type=resolved_entity_type,
        entity_id=resolved_entity_id,
        file_id=file_id,
        metadata=event_metadata,
        message=message,
        legacy_job_id=job_id,
    )


async def record_audit_event(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    file_id: str | None = None,
    actor_user_id: str | None = None,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
    legacy_job_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Append a canonical audit event and return its stored representation.

    Use ``actor_user_id=None`` for automated/system actions. ``entity_id`` is
    polymorphic; ``entity_type`` identifies the referenced entity kind.
    Unknown keyword arguments are logged and ignored rather than raising.
    """
    if kwargs:
        logger.warning(
            "[activity_service] Ignoring unsupported audit arguments",
            arguments=sorted(kwargs),
        )
    if not action or not action.strip():
        raise ValueError("An audit event action is required")
    if not entity_type or not entity_type.strip():
        raise ValueError("An audit event entity_type is required")
    if not entity_id:
        raise ValueError("An audit event entity_id is required")

    event_id = str(uuid4())
    timestamp = datetime.now(UTC).isoformat()
    event_metadata = metadata or {}
    resolved_workspace_id = workspace_id or organization_id
    resolved_organization_id = organization_id or workspace_id
    if legacy_job_id is None and entity_type == "export_job":
        legacy_job_id = entity_id

    payload = {
        "event_id": event_id,
        "id": event_id,
        "action": action,
        "event_name": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "file_id": file_id or (entity_id if entity_type == "file" else None),
        "organization_id": resolved_organization_id,
        "workspace_id": resolved_workspace_id,
        "timestamp": timestamp,
        "created_at": timestamp,
        "job_id": legacy_job_id,
        "project_id": project_id,
        "actor_user_id": actor_user_id,
        "message": message or _default_message(action),
        "metadata": event_metadata,
    }

    try:
        response = await run_in_threadpool(
            lambda: db.table("activity_events").insert(payload).execute()
        )
        if response and response.data:
            logger.info(
                "[activity_service] Event recorded",
                action=action,
                entity_id=entity_id,
            )
            return _shape_activity_row(response.data[0])
        raise RuntimeError("Activity event insert returned no data")
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error(
            "[activity_service] Failed to record event",
            action=action,
            entity_id=entity_id,
            error=str(e),
            exc_info=True,
        )
        raise


async def record_workspace_event(
    *,
    event_name: str,
    workspace_id: str,
    actor_user_id: str,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Record a workspace audit event attributed to its authenticated actor."""
    if not actor_user_id:
        raise ValueError("An authenticated actor_user_id is required")
    if not workspace_id:
        raise ValueError("A workspace_id is required")
    if not event_name or not event_name.strip():
        raise ValueError("An audit event action is required")

    return await record_audit_event(
        action=event_name,
        entity_type="workspace",
        entity_id=workspace_id,
        actor_user_id=actor_user_id,
        organization_id=workspace_id,
        workspace_id=workspace_id,
        metadata=metadata,
        message=message,
    )


async def record_file_event(
    *,
    event_name: str,
    file_id: str,
    actor_user_id: str,
    project_id: str,
    job_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Record a file event using the file ID as the canonical entity reference."""
    if not event_name or not event_name.strip():
        raise ValueError("An audit event action is required")
    if not file_id or not actor_user_id or not project_id:
        raise ValueError("File, actor, and project identifiers are required")

    return await record_audit_event(
        action=event_name,
        entity_type="file",
        entity_id=file_id,
        file_id=file_id,
        actor_user_id=actor_user_id,
        project_id=project_id,
        legacy_job_id=job_id,
        metadata=metadata,
        message=message,
    )


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
        limit = _bounded_limit(limit)
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
                .order("event_id", desc=True)
                .limit(limit)
                .execute()
        )
        rows = response.data if response and response.data else []
        return [_shape_activity_row(r) for r in rows]
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[activity_service] Failed to fetch activity", project_id=project_id, error=str(e), exc_info=True)
        raise


async def get_file_activity(
    file_id: str,
    job_id: str,
    project_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Combine canonical file events and legacy job events for an authorized file."""
    try:
        limit = _bounded_limit(limit)
        if not file_id or not job_id or not project_id:
            raise ValueError("File, job, and project identifiers are required")

        async def read_events(field: str, value: str) -> Any:
            return await run_in_threadpool(
                lambda: db.table("activity_events")
                    .select("*")
                    .eq(field, value)
                    .eq("project_id", project_id)
                    .order("timestamp", desc=True)
                    .order("event_id", desc=True)
                    .limit(limit)
                    .execute()
            )

        file_responses = await asyncio.gather(
            read_events("file_id", file_id),
            read_events("entity_id", file_id),
            read_events("job_id", job_id),
        )

        rows = []
        seen_ids = set()
        for source, response in zip(
            ("file_id", "entity_id", "job_id"),
            file_responses,
            strict=True,
        ):
            for row in response.data if response and response.data else []:
                event_id = row.get("event_id") or row.get("id")
                if event_id and event_id in seen_ids:
                    continue
                if source == "job_id":
                    associated_file_id = row.get("file_id")
                    if associated_file_id and str(associated_file_id) != file_id:
                        continue
                    if (
                        row.get("entity_type") in {"file", "revision"}
                        and row.get("entity_id")
                        and str(row["entity_id"]) != file_id
                    ):
                        continue
                if event_id:
                    seen_ids.add(event_id)
                rows.append(row)

        rows.sort(key=_activity_sort_key, reverse=True)
        return [_shape_activity_row(row) for row in rows[:limit]]
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error(
            "[activity_service] Failed to fetch file activity",
            file_id=file_id,
            error=str(e),
            exc_info=True,
        )
        raise


async def get_workspace_activity(workspace_id: str, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch workspace events only for the owner or a verified member."""
    try:
        limit = _bounded_limit(limit)
        if not workspace_id or not user_id:
            raise ValueError("Workspace and user identifiers are required")
        workspace = await run_in_threadpool(
            lambda: db.table("workspaces").select("owner_id")
                .eq("id", workspace_id)
                .maybe_single().execute()
        )
        if not workspace or not workspace.data:
            logger.warning("[activity_service] Workspace not found", workspace_id=workspace_id)
            return []

        is_owner = workspace.data.get("owner_id") == user_id
        if not is_owner:
            is_member = await run_in_threadpool(
                lambda: db.table("workspace_members").select("user_id")
                    .eq("workspace_id", workspace_id).eq("user_id", user_id)
                    .maybe_single().execute()
            )
            if not is_member or not is_member.data:
                logger.warning(
                    "[activity_service] Not a workspace member",
                    workspace_id=workspace_id,
                    user_id=user_id[:8],
                )
                return []

        responses = await asyncio.gather(*(
            run_in_threadpool(
                lambda field=field: db.table("activity_events")
                    .select("*")
                    .eq(field, workspace_id)
                    .order("timestamp", desc=True)
                    .order("event_id", desc=True)
                    .limit(limit)
                    .execute()
            )
            for field in ("workspace_id", "organization_id")
        ))
        rows_by_id = {
            str(row.get("event_id") or row.get("id")): row
            for response in responses
            for row in (response.data if response and response.data else [])
            if row.get("event_id") or row.get("id")
        }
        rows = sorted(rows_by_id.values(), key=_activity_sort_key, reverse=True)
        return [_shape_activity_row(row) for row in rows[:limit]]
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[activity_service] Failed to fetch workspace activity", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise


def _shape_activity_row(row: dict[str, Any]) -> dict[str, Any]:
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
    job_id: str | None,
    project_id: str | None,
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


def _metadata_entity_id(action: str, metadata: dict[str, Any]) -> str | None:
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