"""
Dashboard endpoints — activity feed + workspace summary.
Owner: Tazwar (queue_owner). Feeds Sunny's UI shells (Step 4/5).
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.queries.job_queries import get_jobs
from app.db.queries.project_queries import get_projects
from app.middlewares.auth import require_auth
from app.schemas.export_contracts import ExportStatus
from app.services.activity_service import get_project_activity
from app.utils.logger import logger
from app.utils.queue_monitor import get_queue_health

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ActivityEvent(BaseModel):
    job_id: str | None = None
    project_id: str
    status: str | None = None
    occurred_at: datetime | None
    event_type: str
    message: str
    event_id: str | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    actor_user_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class ActivityFeedResponse(BaseModel):
    events: list[ActivityEvent]
    total: int


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
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_auth),
):
    """
    Recent job and audit lifecycle events for the authenticated user's projects.
    Ordered by most recent first for the Activity Feed UI.
    """
    try:
        projects = await get_projects(user)
        if project_id:
            projects = [project for project in projects if project["id"] == project_id]

        # The project list is already authenticated and scoped to this user.
        # Activity reads additionally verify each project's ownership because the
        # audit database client uses the service role.
        project_jobs = await asyncio.gather(
            *(get_jobs(project["id"], user) for project in projects)
        )
        raw_jobs = [job for jobs in project_jobs for job in jobs]

        project_activity = await asyncio.gather(
            *(
                get_project_activity(project["id"], user["user_id"], limit=limit)
                for project in projects
            )
        )

        events: list[ActivityEvent] = []
        for job in raw_jobs:
            try:
                status = ExportStatus(job["status"])
            except ValueError:
                continue  # skip any non-contract rows (pre-migration)
            events.append(ActivityEvent(
                job_id=job["id"],
                project_id=job["project_id"],
                status=status,
                occurred_at=job.get("updated_at") or job.get("created_at"),
                event_type="status_change",
                message=_STATUS_LABELS.get(status, status.value),
            ))

        for project_events in project_activity:
            for event in project_events:
                action = event.get("action") or event.get("event_name")
                if not action or not event.get("project_id"):
                    continue
                events.append(ActivityEvent(
                    job_id=event.get("job_id"),
                    project_id=event["project_id"],
                    occurred_at=event.get("timestamp") or event.get("created_at"),
                    event_type=action,
                    message=event.get("message") or action,
                    event_id=event.get("event_id") or event.get("id"),
                    action=action,
                    entity_type=event.get("entity_type"),
                    entity_id=event.get("entity_id"),
                    actor_user_id=event.get("actor_user_id"),
                    metadata=event.get("metadata") or {},
                ))

        events.sort(
            key=lambda event: event.occurred_at.timestamp() if event.occurred_at else 0,
            reverse=True,
        )
        events = events[:limit]
        return ActivityFeedResponse(events=events, total=len(events))

    except Exception as e:
        logger.error(f"Error occurred while fetching activity feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

    except Exception as e:
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

    except Exception as e:
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

    except Exception as e:
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