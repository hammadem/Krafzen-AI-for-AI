import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.supabase_client import db
from app.utils.logger import logger
from app.utils.validators import _user_owns_project


# CREATE JOB
async def create_job(job_data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any] | None:
    #User guard
    if not user or "user_id" not in user:
        logger.warning("[create_job] Invalid user context")
        return {"error": "Invalid user context"}

    try:
        project_id = job_data.get("project_id")

        if not project_id:
            return {"error": "project_id is required"}

        #UUID validation
        try:
            uuid.UUID(project_id)
        except (ValueError, TypeError):
            logger.warning("[create_job] Invalid UUID format", project_id=project_id)
            return {"error": f"Invalid project_id format: {project_id}. Must be a valid UUID."}

        # verify ownership
        owns = await _user_owns_project(project_id, user["user_id"])
        if not owns:
            return {"error": "Unauthorized: You do not own this project"}

        payload = {
            "project_id": project_id,
            "status": job_data.get("status"),
            "transcript": job_data.get("transcript"),
            "error_message": job_data.get("error_message"),
        }

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                .insert(payload)
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[create_job] Job created successfully", job_id=response.data[0]["id"])
            return response.data[0]

        logger.warning("[create_job] Insert failed", project_id=project_id)
        return None

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[create_job] Unexpected error", error=str(e), exc_info=True)
        return {"error": "Unexpected server error"}

# LIST JOBS
async def get_jobs(project_id: str, user: dict[str, Any]) -> list[dict[str, Any]]:
    #User guard
    if not user or "user_id" not in user:
        logger.warning("[get_jobs] Invalid user context")
        return []

    try:
        owns = await _user_owns_project(project_id, user["user_id"])
        if not owns:
            logger.warning("[get_jobs] Unauthorized access attempt", project_id=project_id)
            return []

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                .select("*")
                .eq("project_id", project_id)
                .execute()
        )

        jobs = response.data if response and response.data else []
        logger.debug(f"[get_jobs] Retrieved {len(jobs)} jobs", project_id=project_id)
        return jobs

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[get_jobs] Error", project_id=project_id, error=str(e), exc_info=True)
        return []

# GET SINGLE JOB
async def get_job(job_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    #User guard
    if not user or "user_id" not in user:
        logger.warning("[get_job] Invalid user context")
        return None

    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                .select("*")
                .eq("id", job_id)
                .maybe_single()
                .execute()
        )

        if not response or not response.data:
            logger.warning("[get_job] Job not found", job_id=job_id)
            return None

        job = response.data

        owns = await _user_owns_project(job["project_id"], user["user_id"])
        if not owns:
            logger.warning("[get_job] Unauthorized access attempt", job_id=job_id, project_id=job["project_id"])
            return None

        return job

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[get_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return None

# UPDATE JOB
async def update_job(job_id: str, update_data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any] | None: 
    #User guard
    if not user or "user_id" not in user:
        logger.warning("[update_job] Invalid user context")
        return {"error": "Invalid user context"}

    try:
        job = await get_job(job_id, user)
        if not job:
            return {"error": "Unauthorized or job not found"}

        update_payload = {k: v for k, v in update_data.items() if v is not None}
        update_payload["updated_at"] = datetime.now(UTC).isoformat()

        if not update_payload:
            return {"error": "No valid update fields provided"}

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                .update(update_payload)
                .eq("id", job_id)
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[update_job] Job updated successfully", job_id=job_id)
            return response.data[0]

        logger.warning("[update_job] Update failed", job_id=job_id)
        return {"error": f"Job with id {job_id} not found"}

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[update_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return {"error": str(e)}

# DELETE JOB
async def delete_job(job_id: str, user: dict[str, Any]) -> bool:  
    if not user or "user_id" not in user:
        logger.warning("[delete_job] Invalid user context")
        return False

    try:
        job = await get_job(job_id, user)
        if not job:
            return False

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                .delete()
                .eq("id", job_id)
                .execute()
        )

        success = bool(response and hasattr(response, "data") and response.data)
        if success:
            logger.info("[delete_job] Job deleted successfully", job_id=job_id)
        else:
            logger.warning("[delete_job] Delete failed", job_id=job_id)
        return success

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[delete_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return False