"""
Dashboard endpoints — activity feed + workspace summary.
Owner: Tazwar (queue_owner). Feeds Sunny's UI shells (Step 4/5).
"""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from app.db.queries.job_queries import get_jobs
from app.db.queries.project_queries import get_projects
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.schemas.export_contracts import ExportStatus
from app.utils.logger import logger
from app.utils.queue_monitor import get_queue_health

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ActivityEvent(BaseModel):
    id: str
    job_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    status: str | None = None
    occurred_at: datetime | None = None
    event_type: str
    event_name: str | None = None
    category: str
    actor_user_id: str | None = None
    actor_name: str | None = None
    message: str
    event_id: str | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class ActivityFeedResponse(BaseModel):
    events: list[ActivityEvent]
    total: int
    has_more: bool = False


class WorkspaceSummary(BaseModel):
    total_projects: int
    total_jobs: int
    jobs_by_status: dict   # { "queued": 2, "completed": 5, ... }
    active_jobs: int        # queued + processing + validating + requires_review
    requires_attention: int # requires_review + failed


# Status → human label for the notification message
_STATUS_LABELS = {
    ExportStatus.QUEUED:          "Job queued and waiting to process",
    ExportStatus.PROCESSING:      "Job is being processed",
    ExportStatus.VALIDATING:      "Job is running compliance validation",
    ExportStatus.REQUIRES_REVIEW: "Job requires your review",
    ExportStatus.COMPLETED:       "Job completed successfully",
    ExportStatus.FAILED:          "Job failed — available to retry",
    ExportStatus.CANCELLED:       "Job was cancelled — available to retry",
}

_ACTIVE_STATES = {
    ExportStatus.QUEUED,
    ExportStatus.PROCESSING,
    ExportStatus.VALIDATING,
    ExportStatus.REQUIRES_REVIEW,
}

_ATTENTION_STATES = {
    ExportStatus.REQUIRES_REVIEW,
    ExportStatus.FAILED,
}


@router.get("/activity", response_model=ActivityFeedResponse)
async def get_activity_feed(
    project_id: str | None = Query(None, description="Filter to a specific project"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10_000),
    user=Depends(require_auth),
):
    """
    Recent project and workspace events visible to the authenticated user.
    Ordered by most recent first.
    """
    try:
        page_window = offset + limit + 1
        projects = await get_projects(user, limit=250)
        project_by_id = {str(project["id"]): project for project in projects}
        if project_id and project_id not in project_by_id:
            return ActivityFeedResponse(events=[], total=0, has_more=False)
        visible_projects = (
            [project_by_id[project_id]] if project_id else projects
        )
        project_ids = [str(project["id"]) for project in visible_projects]

        job_limit = asyncio.Semaphore(8)

        async def jobs_for_project(owned_project_id: str) -> list[dict]:
            async with job_limit:
                return await get_jobs(owned_project_id, user, limit=page_window)

        job_groups = await asyncio.gather(
            *(jobs_for_project(owned_project_id) for owned_project_id in project_ids)
        )
        raw_jobs = [job for group in job_groups for job in group]

        workspace_ids = await _get_user_workspace_ids(user["user_id"])
        activity_rows = await _get_activity_rows(project_ids, workspace_ids, page_window)

        events: list[ActivityEvent] = []
        recorded_job_statuses = {
            (str(row.get("job_id")), row.get("event_name") or row.get("action"))
            for row in activity_rows
            if row.get("job_id") and (row.get("event_name") or row.get("action"))
        }

        for row in activity_rows:
            event_name = row.get("event_name") or row.get("action") or "activity.updated"
            row_project_id = row.get("project_id")
            if project_id and str(row_project_id or "") != project_id:
                continue
            project = project_by_id.get(str(row_project_id)) if row_project_id else None
            metadata = row.get("metadata") or {}
            actor_user_id = row.get("actor_user_id")
            events.append(ActivityEvent(
                id=str(row.get("id") or row.get("event_id") or f"{event_name}-{row.get('created_at', '')}"),
                job_id=str(row["job_id"]) if row.get("job_id") else None,
                project_id=str(row_project_id) if row_project_id else None,
                project_name=_project_display_name(project),
                occurred_at=row.get("created_at") or row.get("timestamp"),
                event_type=event_name,
                event_name=event_name,
                category=_activity_category(event_name),
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                actor_name=None,
                event_id=str(row.get("event_id") or row.get("id"))
                if row.get("event_id") or row.get("id")
                else None,
                action=row.get("action") or event_name,
                entity_type=row.get("entity_type"),
                entity_id=str(row["entity_id"]) if row.get("entity_id") else None,
                message=_activity_message(
                    event_name,
                    metadata,
                    None,
                    {},
                    row.get("message"),
                ),
                metadata=metadata,
            ))

        for job in raw_jobs:
            try:
                status = ExportStatus(job["status"])
            except ValueError:
                continue  # skip any non-contract rows (pre-migration)
            job_id = str(job["id"])
            if (job_id, f"export.{status.value}") in recorded_job_statuses:
                continue
            project = project_by_id.get(str(job["project_id"]))
            actor_user_id = project.get("user_id") if project else None
            events.append(ActivityEvent(
                id=job_id,
                job_id=job_id,
                project_id=str(job["project_id"]),
                project_name=_project_display_name(project),
                status=status.value,
                occurred_at=job.get("updated_at") or job.get("created_at"),
                event_type="status_change",
                event_name=f"export.{status.value}",
                category="exports",
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                actor_name=None,
                message=_STATUS_LABELS.get(status, status.value),
                metadata={},
            ))

        events.sort(key=_event_time_sort_key, reverse=True)
        has_more = len(events) > offset + limit
        page_events = events[offset:offset + limit]
        actor_names = await _get_actor_names(
            [
                {"actor_user_id": event.actor_user_id, "metadata": event.metadata}
                for event in page_events
            ],
            visible_projects,
        )
        for event in page_events:
            event.actor_name = (
                actor_names.get(str(event.actor_user_id))
                if event.actor_user_id
                else None
            )
            event.message = _activity_message(
                event.event_name or event.event_type,
                event.metadata,
                event.actor_name,
                actor_names,
                event.message,
            )
        return ActivityFeedResponse(
            events=page_events,
            total=len(page_events),
            has_more=has_more,
        )

    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error occurred while fetching activity feed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve activity feed.",
        ) from e


async def _get_user_workspace_ids(user_id: str) -> list[str]:
    owned, memberships = await asyncio.gather(
        run_in_threadpool(
            lambda: db.table("workspaces").select("id").eq("owner_id", user_id).execute()
        ),
        run_in_threadpool(
            lambda: db.table("workspace_members").select("workspace_id")
                .eq("user_id", user_id).execute()
        ),
    )
    return list({
        str(row["id"]) for row in (owned.data or [])
    } | {
        str(row["workspace_id"]) for row in (memberships.data or [])
    })


async def _get_activity_rows(
    project_ids: list[str],
    workspace_ids: list[str],
    fetch_limit: int,
) -> list[dict]:
    queries = []
    if project_ids:
        queries.append(
            run_in_threadpool(
                lambda: db.table("activity_events").select("*")
                    .in_("project_id", project_ids)
                    .order("created_at", desc=True)
                    .order("id", desc=True)
                    .range(0, fetch_limit - 1)
                    .execute()
            )
        )
    if workspace_ids:
        queries.append(
            run_in_threadpool(
                lambda: db.table("activity_events").select("*")
                    .in_("workspace_id", workspace_ids)
                    .order("created_at", desc=True)
                    .order("id", desc=True)
                    .range(0, fetch_limit - 1)
                    .execute()
            )
        )
    responses = await asyncio.gather(*queries) if queries else []
    deduplicated = {
        str(row.get("id") or row.get("event_id")): row
        for response in responses
        for row in (response.data or [])
    }
    return list(deduplicated.values())


async def _get_actor_names(
    activity_rows: list[dict],
    projects: list[dict],
) -> dict[str, str]:
    actor_ids = {
        str(row["actor_user_id"])
        for row in activity_rows
        if row.get("actor_user_id")
    }
    for row in activity_rows:
        target_user_id = (row.get("metadata") or {}).get("target_user_id")
        if target_user_id:
            actor_ids.add(str(target_user_id))
    actor_ids.update(
        str(project["user_id"])
        for project in projects
        if project.get("user_id")
    )

    semaphore = asyncio.Semaphore(10)

    async def get_name(actor_id: str) -> tuple[str, str | None]:
        async with semaphore:
            try:
                response = await run_in_threadpool(
                    lambda: db.auth.admin.get_user_by_id(actor_id)
                )
                auth_user = response.user if response else None
                metadata = auth_user.user_metadata if auth_user else {}
                full_name = metadata.get("full_name") or metadata.get("name")
                if not full_name:
                    full_name = " ".join(
                        part for part in (
                            metadata.get("firstname") or metadata.get("first_name"),
                            metadata.get("lastname") or metadata.get("last_name"),
                        ) if part
                    )
                return actor_id, full_name or (auth_user.email if auth_user else None)
            except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
                logger.warning(
                    "Could not load activity actor name",
                    actor_user_id=actor_id,
                    error=str(e),
                )
                return actor_id, None

    names = await asyncio.gather(*(get_name(actor_id) for actor_id in actor_ids))
    return {actor_id: name for actor_id, name in names if name}


def _project_display_name(project: dict | None) -> str | None:
    if not project:
        return None
    name = project.get("name") or project.get("project_name") or project.get("input_text")
    if isinstance(name, str) and len(name) > 72:
        return f"{name[:69]}..."
    return name


def _event_time_sort_key(event: ActivityEvent) -> tuple[float, str]:
    timestamp = event.occurred_at
    if timestamp is None:
        return float("-inf"), event.id
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.timestamp(), event.id


def _activity_category(event_name: str) -> str:
    if event_name.startswith(("file.", "upload.")):
        return "files"
    if event_name.startswith("ai."):
        return "ai"
    if event_name.startswith("revision."):
        return "revisions"
    if event_name.startswith(("team.", "member.")):
        return "team"
    if event_name.startswith(("permissions.", "permission.")):
        return "permissions"
    if event_name.startswith("export."):
        return "exports"
    return "all"


def _activity_message(
    event_name: str,
    metadata: dict,
    actor_name: str | None = None,
    actor_names: dict[str, str] | None = None,
    fallback: str | None = None,
) -> str:
    target_user_id = metadata.get("target_user_id")
    target = (
        (actor_names or {}).get(str(target_user_id))
        or metadata.get("target_user_name")
        or metadata.get("target_email")
    )
    if event_name == "team.role_changed":
        target = target or "member"
        old_role = metadata.get("from_role", "previous role")
        new_role = metadata.get("to_role", "new role")
        actor = actor_name or "A team member"
        return f"{actor} changed {target}'s role from {old_role.title()} to {new_role.title()}"
    if event_name == "team.member_removed":
        actor = actor_name or "A team member"
        return f"{actor} removed {target or 'a member'} from the workspace"
    if event_name == "team.member_invited":
        actor = actor_name or "A team member"
        return f"{actor} invited {target or 'a new member'} to the workspace"
    if event_name == "team.member_joined":
        return f"{actor_name or target or 'A team member'} joined the workspace"
    if event_name == "permissions.permission_changed" and target:
        old_role = metadata.get("from_role", "previous role")
        new_role = metadata.get("to_role", "new role")
        actor = actor_name or "A team member"
        return f"{actor} changed {target}'s permissions from {old_role.title()} to {new_role.title()}"
    if event_name == "permissions.access_granted":
        return f"Workspace access granted to {target or 'a member'}"
    if event_name == "permissions.access_revoked":
        return f"Workspace access revoked for {target or 'a member'}"
    return fallback or event_name.replace(".", " ").replace("_", " ").capitalize()


@router.get("/workspace-summary", response_model=WorkspaceSummary)
async def get_workspace_summary(user=Depends(require_auth)):
    """
    Aggregate workspace stats for the authenticated user.
    Used by Sunny's workspace summary panel (Step 5).
    """
    try:
        projects = await get_projects(user)
        total_projects = len(projects)

        all_jobs = []
        for p in projects:
            jobs = await get_jobs(p["id"], user)
            all_jobs.extend(jobs)

        jobs_by_status: dict = {s.value: 0 for s in ExportStatus}
        for job in all_jobs:
            try:
                s = ExportStatus(job["status"])
                jobs_by_status[s.value] += 1
            except ValueError:
                pass  # skip pre-migration rows

        active = sum(jobs_by_status[s.value] for s in _ACTIVE_STATES)
        attention = sum(jobs_by_status[s.value] for s in _ATTENTION_STATES)

        return WorkspaceSummary(
            total_projects=total_projects,
            total_jobs=len(all_jobs),
            jobs_by_status=jobs_by_status,
            active_jobs=active,
            requires_attention=attention,
        )

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error(f"Error occurred while fetching workspace summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Notifications ────────────────────────────────────────────────────────────

# Notification type derives from job status
_STATUS_TO_NOTIF_TYPE = {
    ExportStatus.COMPLETED:       "success",
    ExportStatus.FAILED:          "error",
    ExportStatus.REQUIRES_REVIEW: "warning",
    ExportStatus.QUEUED:          "info",
    ExportStatus.PROCESSING:      "info",
    ExportStatus.VALIDATING:      "info",
    ExportStatus.CANCELLED:       "info",
}

_STATUS_TO_NOTIF_TITLE = {
    ExportStatus.COMPLETED:       "Export completed",
    ExportStatus.FAILED:          "Export failed",
    ExportStatus.REQUIRES_REVIEW: "Review required",
    ExportStatus.QUEUED:          "Export queued",
    ExportStatus.PROCESSING:      "Processing started",
    ExportStatus.VALIDATING:      "Validation in progress",
    ExportStatus.CANCELLED:       "Export cancelled",
}


class NotificationItem(BaseModel):
    id: str                    # job_id — stable identifier Sunny can key on
    title: str                 # e.g. "Export completed"
    message: str               # same human label as activity feed
    read: bool                 # always False on creation; toggled via PATCH below
    created_at: datetime | None
    type: str                  # "success" | "error" | "warning" | "info"


class NotificationsResponse(BaseModel):
    notifications: list[NotificationItem]
    total: int


@router.get("/notifications", response_model=NotificationsResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    user=Depends(require_auth),
):
    """
    Notification feed for the authenticated user.
    Derived from job lifecycle events. Used by Sunny's notification UI shell.
    Response: { notifications: [{ id, title, message, read, created_at, type }], total }
    """
    try:
        projects = await get_projects(user)
        all_jobs = []
        for p in projects:
            jobs = await get_jobs(p["id"], user)
            all_jobs.extend(jobs)

        # Sort by most recent first
        all_jobs.sort(
            key=lambda j: j.get("updated_at") or j.get("created_at") or "",
            reverse=True,
        )

        notifications = []
        for job in all_jobs:
            try:
                status = ExportStatus(job["status"])
            except ValueError:
                continue

            # Only surface statuses that are meaningful as notifications
            if status not in _STATUS_TO_NOTIF_TYPE:
                continue

            # read state: completed/failed/requires_review/cancelled are "unread" by default
            # processing/validating/queued are informational — mark as read (not alerting)
            is_unread = status in {
                ExportStatus.COMPLETED,
                ExportStatus.FAILED,
                ExportStatus.REQUIRES_REVIEW,
                ExportStatus.CANCELLED,
            }

            if unread_only and not is_unread:
                continue

            notifications.append(NotificationItem(
                id=job["id"],
                title=_STATUS_TO_NOTIF_TITLE.get(status, status.value),
                message=_STATUS_LABELS.get(status, status.value),
                read=not is_unread,
                created_at=job.get("updated_at") or job.get("created_at"),
                type=_STATUS_TO_NOTIF_TYPE.get(status, "info"),
            ))

        notifications = notifications[:limit]
        return NotificationsResponse(notifications=notifications, total=len(notifications))

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user=Depends(require_auth),
):
    """
    Mark a notification (job event) as read.
    notification_id is the job_id (same as the id field in NotificationItem).
    Week 1: stores read state on the job's error_message field is NOT correct —
    this is a stub that returns 200 so Sunny can wire the UI now.
    Week 2: add a notifications table with per-user read state.
    """
    # Verify the job exists and belongs to this user before returning 200
    from app.db.queries.job_queries import get_job
    job = await get_job(notification_id, user)
    if not job:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Week 2: persist read=True to notifications table here
    logger.info(
        "[mark_notification_read] Read state acknowledged (persistence in Week 2)",
        notification_id=notification_id,
        user_id=user["user_id"],
    )
    return {"id": notification_id, "read": True}


# ── Members list ─────────────────────────────────────────────────────────────

class MemberItem(BaseModel):
    user_id: str
    email: str | None = None
    display_name: str | None = None
    role: str = "member"       # "owner" | "member" — extend when roles table exists


class MembersResponse(BaseModel):
    members: list[MemberItem]
    total: int


@router.get("/members", response_model=MembersResponse)
async def get_workspace_members(user=Depends(require_auth)):
    """
    Workspace members list for the authenticated user's workspace.
    Step 6 — Sunny's members UI shell.
    Currently returns the authenticated user only (single-user workspaces in Week 1).
    Extend when a workspace_members table is added.
    Response: { members: [{ user_id, email, display_name, role }], total }
    """
    try:
        # Week 1: workspaces are single-user (no members table yet).
        # Return the authed user as owner. Sunny can wire the shape now;
        # we extend this when multi-user workspace support lands.
        member = MemberItem(
            user_id=user["user_id"],
            email=user.get("email"),
            display_name=user.get("user_metadata", {}).get("full_name")
                         or user.get("email"),
            role="owner",
        )
        return MembersResponse(members=[member], total=1)

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))


class QueueHealthResponse(BaseModel):
    counts_by_status: dict
    stuck_jobs: int
    stuck_job_ids: list[str]
    unknown_status_rows: int
    threshold_minutes: int
    assessed_at: str
    error: str | None = None


@router.get("/queue-health", response_model=QueueHealthResponse)
async def queue_health_endpoint(user=Depends(require_auth)):
    """
    Live queue health snapshot.
    Returns counts by status, stuck job count, and unknown-status rows
    (non-zero unknown rows means the contract migration hasn't run).
    Week 3 will expand with avg processing time, failure rate, retry frequency.
    Owner: Tazwar — monitoring foundation per Week 1 Step 6.
    """
    result = await get_queue_health()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result