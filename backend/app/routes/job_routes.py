from fastapi import APIRouter, HTTPException, Header, Query
from typing import List
from app.db.queries.job_queries import (
    create_job as create_job_query,
    get_jobs,
    get_job,
    update_job,
    delete_job
)
from app.models.job_model import JobCreate, JobUpdate, JobResponse
from app.core.config import settings

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# 🟢 Create Job
@router.post("/", response_model=JobResponse, status_code=201)
async def create_job_route(job: JobCreate, authorization: str = Header(None)):
    result = await create_job_query(job.dict(), authorization)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error", "Job creation failed"))
    return result


# 🟡 Get All Jobs (by project_id)
@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    project_id: str = Query(..., description="Filter jobs by project_id"),
    authorization: str = Header(None)
):
    jobs = await get_jobs(project_id, authorization)
    return jobs


# 🟢 Get Single Job
@router.get("/{job_id}", response_model=JobResponse)
async def get_job_route(job_id: str, authorization: str = Header(None)):
    job = await get_job(job_id, authorization)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# 🟣 Update Job (PATCH)
@router.patch("/{job_id}", response_model=JobResponse)
async def update_job_route(job_id: str, updates: JobUpdate, authorization: str = Header(None)):
    updated = await update_job(job_id, updates.dict(exclude_unset=True), authorization)
    if not updated or updated.get("error"):
        raise HTTPException(status_code=400, detail=updated.get("error", "Job update failed"))
    return updated


# 🔴 Delete Job
@router.delete("/{job_id}")
async def delete_job_route(job_id: str, authorization: str = Header(None)):
    deleted = await delete_job(job_id, authorization)
    if not deleted:
        raise HTTPException(status_code=400, detail="Job deletion failed")
    return {"message": "Job deleted successfully"}


# 🧩 Debug endpoint (optional)
@router.get("/debug/env")
async def debug_env():
    return {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SERVICE_ROLE_KEY": settings.SUPABASE_SERVICE_ROLE_KEY[:8] + "...",
        "ANON": settings.SUPABASE_ANON_KEY[:8] + "..."
    }
