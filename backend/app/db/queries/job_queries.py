from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
<<<<<<< HEAD
=======
from app.utils.logger import logger
import uuid
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9


async def create_job(job_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
<<<<<<< HEAD
        token = None
        if authorization:
            parts = authorization.split(" ")
            if len(parts) == 2:
                token = parts[1]

        project_id = job_data.get("project_id")
        if not project_id:
            print("[create_job] Missing project_id in payload")
            return {"error": "project_id is required"}
=======
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
        
        # Validate UUID format
        try:
            uuid.UUID(project_id)
        except (ValueError, TypeError):
            logger.warning("[create_job] Invalid UUID format", project_id=project_id)
            return {"error": f"Invalid project_id format: {project_id}. Must be a valid UUID."}
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9

        project_check = await run_in_threadpool(
            lambda: db.table("projects")
                        .select("id")
                        .eq("id", project_id)
                        .maybe_single()
                        .execute()
        )

<<<<<<< HEAD
        if not project_check.data:
            print(f"[create_job] Project {project_id} not found")
=======
        if not project_check or not hasattr(project_check, 'data') or not project_check.data:
            logger.warning("[create_job] Project not found", project_id=project_id)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
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

<<<<<<< HEAD
        return response.data[0] if response.data else None

    except Exception as e:
        error_msg = str(e)
        if "foreign key constraint" in error_msg.lower():
            print("[create_job] Foreign key violation")
            return {"error": "Invalid project_id. Project not found"}
        print(f"[create_job] Unexpected error: {e}")
=======
        return response.data[0] if response and hasattr(response, 'data') and response.data else None

    except Exception as e:
        error_msg = str(e)
        # Check for invalid UUID or Supabase client errors
        if "missing response" in error_msg.lower() or "postgrest" in error_msg.lower() or "204" in error_msg:
            logger.warning("[create_job] Invalid UUID or database error", project_id=job_data.get("project_id"), error=error_msg)
            return {"error": "Invalid project_id format or database error"}
        if "foreign key constraint" in error_msg.lower():
            logger.warning("[create_job] Foreign key violation", project_id=job_data.get("project_id"))
            return {"error": "Invalid project_id. Project not found"}
        logger.error("[create_job] Unexpected error", error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return {"error": "Unexpected server error"}


async def get_jobs(project_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .select("*")
                        .eq("project_id", project_id)
                        .execute()
        )
<<<<<<< HEAD
        return response.data or []
    except Exception as e:
        print(f"[get_jobs] Error: {e}")
=======
        return response.data if response and hasattr(response, 'data') and response.data else []
    except Exception as e:
        logger.error("[get_jobs] Error", project_id=project_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
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
<<<<<<< HEAD
        return response.data
    except Exception as e:
        print(f"[get_job] Error: {e}")
=======
        if not response or not hasattr(response, 'data') or not response.data:
            return None
        return response.data
    except Exception as e:
        logger.error("[get_job] Error", job_id=job_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return None


async def update_job(job_id: str, update_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
<<<<<<< HEAD
            print("[update_job] Missing update data")
            return {"error": "No update fields provided"}

        # Clean out None values
        update_payload = {k: v for k, v in update_data.items() if v is not None}
=======
            logger.warning("[update_job] Missing update data", job_id=job_id)
            return {"error": "No update fields provided"}

        # Clean out None values and add updated_at
        from datetime import datetime
        update_payload = {k: v for k, v in update_data.items() if v is not None}
        update_payload["updated_at"] = datetime.utcnow().isoformat()
        
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        if not update_payload:
            return {"error": "No valid update fields provided"}

        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .update(update_payload)
                        .eq("id", job_id)
                        .execute()
        )

<<<<<<< HEAD
        if response and response.data:
            return response.data[0]

        print(f"[update_job] No job found with id {job_id}")
        return {"error": f"Job with id {job_id} not found"}

    except Exception as e:
        print(f"[update_job] Error: {e}")
=======
        if response and hasattr(response, 'data') and response.data and len(response.data) > 0:
            return response.data[0]

        logger.warning("[update_job] Job not found", job_id=job_id)
        return {"error": f"Job with id {job_id} not found"}

    except Exception as e:
        logger.error("[update_job] Error", job_id=job_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return {"error": str(e)}


async def delete_job(job_id: str, authorization: Optional[str] = None) -> bool:
    try:
        response = await run_in_threadpool(
            lambda: db.table("jobs")
                        .delete()
                        .eq("id", job_id)
                        .execute()
        )
<<<<<<< HEAD
        return bool(response.data)
    except Exception as e:
        print(f"[delete_job] Error: {e}")
=======
        return bool(response and hasattr(response, 'data') and response.data)
    except Exception as e:
        logger.error("[delete_job] Error", job_id=job_id, error=str(e), exc_info=True)
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9
        return False
