from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger


async def create_job(job_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        # Validate authorization format
        if authorization:
            if not authorization.startswith("Bearer "):
                logger.warning("[create_job] Invalid authorization format", authorization_format=authorization[:20] + "...")
                return {"error": "Invalid authorization format. Expected 'Bearer <token>'"}
            # TODO: Implement full JWT validation against Supabase
            # For now, we validate format but don't verify the token
            token = authorization.split(" ")[1]
            logger.debug("[create_job] Authorization token provided", token_length=len(token))

        project_id = job_data.get("project_id")
        if not project_id:
            logger.warning("[create_job] Missing project_id in payload")
            return {"error": "project_id is required"}

        project_check = await run_in_threadpool(
            lambda: db.table("projects")
                        .select("id")
                        .eq("id", project_id)
                        .maybe_single()
                        .execute()
        )

        if not project_check.data:
            logger.warning("[create_job] Project not found", project_id=project_id)
            return {"error": f"Project with id {project_id} does not exist"}

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

        return response.data[0] if response.data else None

    except Exception as e:
        error_msg = str(e)
        if "foreign key constraint" in error_msg.lower():
            logger.error("[create_job] Foreign key violation", project_id=job_data.get("project_id"), exc_info=True)
            return {"error": "Invalid project_id. Project not found"}
        logger.error("[create_job] Unexpected error", error=str(e), exc_info=True)
        return {"error": "Unexpected server error"}


async def get_jobs(project_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .select("*")
                        .eq("project_id", project_id)
                        .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error("[get_jobs] Error", project_id=project_id, error=str(e), exc_info=True)
        return []


async def get_job(job_id: str, authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .select("*")
                        .eq("id", job_id)
                        .maybe_single()
                        .execute()
        )
        return response.data
    except Exception as e:
        logger.error("[get_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return None


async def update_job(job_id: str, update_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
            logger.warning("[update_job] Missing update data", job_id=job_id)
            return {"error": "No update fields provided"}

        # Clean out None values and add updated_at
        from datetime import datetime
        update_payload = {k: v for k, v in update_data.items() if v is not None}
        update_payload["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_payload:
            return {"error": "No valid update fields provided"}

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .update(update_payload)
                        .eq("id", job_id)
                        .execute()
        )

        if response and response.data:
            return response.data[0]

        logger.warning("[update_job] Job not found", job_id=job_id)
        return {"error": f"Job with id {job_id} not found"}

    except Exception as e:
        logger.error("[update_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return {"error": str(e)}


async def delete_job(job_id: str, authorization: Optional[str] = None) -> bool:
    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .delete()
                        .eq("id", job_id)
                        .execute()
        )
        return bool(response.data)
    except Exception as e:
        logger.error("[delete_job] Error", job_id=job_id, error=str(e), exc_info=True)
        return False
