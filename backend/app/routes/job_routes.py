from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from typing import List, Optional
from app.db.queries.job_queries import (
    create_job as create_job_query,
    get_jobs,
    get_job,
    update_job,
    delete_job
)
from app.models.job_model import JobCreate, JobUpdate, JobResponse
from app.middlewares.auth import require_auth
from app.services.queue_service import advance_job_status, enqueue_job, retry_job
from app.schemas.export_contracts import ExportStatus

class StatusAdvanceRequest(BaseModel):
    status: ExportStatus
    error_message: Optional[str] = None

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job_route(
    job: JobCreate,
    user=Depends(require_auth)
):
    result = await create_job_query(job.model_dump(), user)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error", "Job creation failed"))
    return result


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    project_id: str = Query(..., description="Filter jobs by project_id"),
    user=Depends(require_auth)
):
    jobs = await get_jobs(project_id, user)
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_route(
    job_id: str,
    user=Depends(require_auth)
):
    job = await get_job(job_id, user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job_route(
    job_id: str,
    updates: JobUpdate,
    user=Depends(require_auth)
):
    updated = await update_job(job_id, updates.model_dump(exclude_unset=True), user)
    if not updated or updated.get("error"):
        raise HTTPException(status_code=400, detail=updated.get("error", "Job update failed"))
    return updated


@router.delete("/{job_id}")
async def delete_job_route(
    job_id: str,
    user=Depends(require_auth)
):
    deleted = await delete_job(job_id, user)
    if not deleted:
        raise HTTPException(status_code=400, detail="Job deletion failed")
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/advance", response_model=JobResponse)
async def advance_job_status_route(
    job_id: str,
    body: StatusAdvanceRequest,
    user=Depends(require_auth),
):
    """
    Advance a job to the next lifecycle status.
    Only contract-aligned transitions are accepted.
    Source of truth: /api/v1/contracts/export-lifecycle
    """
    result = await advance_job_status(job_id, body.status, user, body.error_message)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error", "Status transition failed"))
    return result


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job_route(
    job_id: str,
    user=Depends(require_auth),
):
    """
    Re-queue a FAILED or CANCELLED job.
    Retryable states: failed, cancelled (per /api/v1/contracts/export-lifecycle)
    """
    result = await retry_job(job_id, user)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error", "Retry failed"))
    return result