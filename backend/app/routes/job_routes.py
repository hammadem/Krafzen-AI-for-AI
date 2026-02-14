from fastapi import APIRouter, HTTPException, Header, Query, Depends
from typing import List
from app.db.queries.job_queries import (
    create_job as create_job_query,
    get_jobs,
    get_job,
    update_job,
    delete_job
)
from app.models.job_model import JobCreate, JobUpdate, JobResponse
from app.middlewares.auth import require_auth

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
