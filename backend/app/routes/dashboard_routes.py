"""
Dashboard endpoints — activity feed + workspace summary.
Owner: Tazwar (queue_owner). Feeds Sunny's UI shells (Step 4/5).
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.middlewares.auth import require_auth
from app.schemas.export_contracts import ExportStatus
from app.db.queries.job_queries import get_jobs
from app.db.queries.project_queries import get_projects

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ActivityEvent(BaseModel):
    job_id: str
    project_id: str
    status: ExportStatus
    occurred_at: Optional[datetime]
    event_type: str        # "status_change" always for now; extendable
    message: str           # human-readable label for the notification UI


class ActivityFeedResponse(BaseModel):
    events: List[ActivityEvent]
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
    project_id: Optional[str] = Query(None, description="Filter to a specific project"),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_auth),
):
    """
    Recent job lifecycle events for the authenticated user.
    Ordered by most recent first. Used by Sunny's activity feed / notifications UI.
    """
    try:
        # get_jobs filters by project_id and scopes to user via RLS
        if project_id:
            raw_jobs = await get_jobs(project_id, user)
        else:
            # fetch all projects first, then gather jobs across them
            projects = await get_projects(user)
            raw_jobs = []
            for p in projects:
                jobs = await get_jobs(p["id"], user)
                raw_jobs.extend(jobs)

        # sort by updated_at descending, apply limit
        raw_jobs.sort(
            key=lambda j: j.get("updated_at") or j.get("created_at") or "",
            reverse=True,
        )
        raw_jobs = raw_jobs[:limit]

        events = []
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

        return ActivityFeedResponse(events=events, total=len(events))

    except Exception as e:
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
        raise HTTPException(status_code=500, detail=str(e))