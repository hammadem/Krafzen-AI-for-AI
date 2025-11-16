from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
<<<<<<< HEAD


# CREATE
async def create_file(file_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        job_id = file_data.get("job_id")
        if not job_id:
            print("[create_file] Missing job_id in payload")
            return {"error": "job_id is required"}
=======
from app.utils.logger import logger
import uuid


# CREATE
async def create_file(file_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        job_id = file_data.get("job_id")
        if not job_id:
            logger.warning("[create_file] Missing job_id in payload")
            return {"error": "job_id is required"}
        
        # Validate UUID format
        try:
            uuid.UUID(job_id)
        except (ValueError, TypeError):
            logger.warning("[create_file] Invalid UUID format", job_id=job_id)
            return {"error": f"Invalid job_id format: {job_id}. Must be a valid UUID."}
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9

        # Check if the job exists
        job_check = await run_in_threadpool(
            lambda: db.table("jobs")
                    .select("id")
                    .eq("id", job_id)
                    .maybe_single()
                    .execute()
        )

<<<<<<< HEAD
        if not job_check.data:
            print(f"[create_file] Job {job_id} not found")
=======
        if not job_check or not hasattr(job_check, 'data') or not job_check.data:
            logger.warning("[create_file] Job not found", job_id=job_id)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
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

<<<<<<< HEAD
        return response.data[0] if response.data else None

    except Exception as e:
        print(f"[create_file] Error: {e}")
=======
        return response.data[0] if response and hasattr(response, 'data') and response.data else None

    except Exception as e:
        error_msg = str(e)
        # Check for invalid UUID or Supabase client errors
        if "missing response" in error_msg.lower() or "postgrest" in error_msg.lower() or "204" in error_msg:
            logger.warning("[create_file] Invalid UUID or database error", job_id=file_data.get("job_id"), error=error_msg)
            return {"error": "Invalid job_id format or database error"}
        logger.error("[create_file] Error", job_id=file_data.get("job_id"), error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return {"error": str(e)}


# READ (List all files for a job)
<<<<<<< HEAD
async def get_files(job_id: str) -> List[Dict[str, Any]]:
=======
async def get_files(job_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .select("*")
                    .eq("job_id", job_id)
                    .execute()
        )
<<<<<<< HEAD
        return response.data or []
    except Exception as e:
        print(f"[get_files] Error: {e}")
=======
        return response.data if response and hasattr(response, 'data') and response.data else []
    except Exception as e:
        logger.error("[get_files] Error", job_id=job_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return []


# READ (Single file by ID)
<<<<<<< HEAD
async def get_file(file_id: str) -> Optional[Dict[str, Any]]:
=======
async def get_file(file_id: str, authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .select("*")
                    .eq("id", file_id)
                    .maybe_single()
                    .execute()
        )
<<<<<<< HEAD
        return response.data
    except Exception as e:
        print(f"[get_file] Error: {e}")
=======
        if not response or not hasattr(response, 'data') or not response.data:
            return None
        return response.data
    except Exception as e:
        logger.error("[get_file] Error", file_id=file_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return None


# UPDATE
<<<<<<< HEAD
async def update_file(file_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
            print("[update_file] Missing update data")
=======
async def update_file(file_id: str, update_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
            logger.warning("[update_file] Missing update data", file_id=file_id)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
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

<<<<<<< HEAD
        if response and response.data:
            return response.data[0]

        print(f"[update_file] No file found with id {file_id}")
        return {"error": f"File with id {file_id} not found"}

    except Exception as e:
        print(f"[update_file] Error: {e}")
=======
        if response and hasattr(response, 'data') and response.data and len(response.data) > 0:
            return response.data[0]

        logger.warning("[update_file] File not found", file_id=file_id)
        return {"error": f"File with id {file_id} not found"}

    except Exception as e:
        logger.error("[update_file] Error", file_id=file_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return {"error": str(e)}


# DELETE
<<<<<<< HEAD
async def delete_file(file_id: str) -> bool:
=======
async def delete_file(file_id: str, authorization: Optional[str] = None) -> bool:
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
    try:
        response = await run_in_threadpool(
            lambda: db.table("files")
                    .delete()
                    .eq("id", file_id)
                    .execute()
        )
<<<<<<< HEAD
        return bool(response.data)
    except Exception as e:
        print(f"[delete_file] Error: {e}")
=======
        return bool(response and hasattr(response, 'data') and response.data)
    except Exception as e:
        logger.error("[delete_file] Error", file_id=file_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return False
