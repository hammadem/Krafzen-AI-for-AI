from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger


# CREATE
async def create_file(file_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        job_id = file_data.get("job_id")
        if not job_id:
            logger.warning("[create_file] Missing job_id in payload")
            return {"error": "job_id is required"}

        # Check if the job exists
        job_check = await run_in_threadpool(
            lambda: db.table("jobs")
                    .select("id")
                    .eq("id", job_id)
                    .maybe_single()
                    .execute()
        )

        if not job_check.data:
            logger.warning("[create_file] Job not found", job_id=job_id)
            return {"error": f"Job with id {job_id} does not exist"}

        payload = {
            "job_id": job_id,
            "file_url": file_data.get("file_url"),
            "file_type": file_data.get("file_type"),
        }

        response = await run_in_threadpool(
            lambda: db.table("files")
                    .insert(payload)
                    .execute()
        )

        return response.data[0] if response.data else None

    except Exception as e:
        logger.error("[create_file] Error", job_id=file_data.get("job_id"), error=str(e), exc_info=True)
        return {"error": str(e)}


# READ (List all files for a job)
async def get_files(job_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .select("*")
                    .eq("job_id", job_id)
                    .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error("[get_files] Error", job_id=job_id, error=str(e), exc_info=True)
        return []


# READ (Single file by ID)
async def get_file(file_id: str, authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .select("*")
                    .eq("id", file_id)
                    .maybe_single()
                    .execute()
        )
        return response.data
    except Exception as e:
        logger.error("[get_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return None


# UPDATE
async def update_file(file_id: str, update_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
            logger.warning("[update_file] Missing update data", file_id=file_id)
            return {"error": "No update fields provided"}

        update_payload = {k: v for k, v in update_data.items() if v is not None}
        if not update_payload:
            return {"error": "No valid fields provided"}

        response = await run_in_threadpool(
            lambda: db.table("files")
                    .update(update_payload)
                    .eq("id", file_id)
                    .execute()
        )

        if response and response.data:
            return response.data[0]

        logger.warning("[update_file] File not found", file_id=file_id)
        return {"error": f"File with id {file_id} not found"}

    except Exception as e:
        logger.error("[update_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return {"error": str(e)}


# DELETE
async def delete_file(file_id: str, authorization: Optional[str] = None) -> bool:
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .delete()
                    .eq("id", file_id)
                    .execute()
        )
        return bool(response.data)
    except Exception as e:
        logger.error("[delete_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return False
