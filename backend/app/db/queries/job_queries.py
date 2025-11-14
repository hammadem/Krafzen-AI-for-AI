from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db


async def create_job(job_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        token = None
        if authorization:
            parts = authorization.split(" ")
            if len(parts) == 2:
                token = parts[1]

        project_id = job_data.get("project_id")
        if not project_id:
            print("[create_job] Missing project_id in payload")
            return {"error": "project_id is required"}

        project_check = await run_in_threadpool(
            lambda: db.table("projects")
                        .select("id")
                        .eq("id", project_id)
                        .maybe_single()
                        .execute()
        )

        if not project_check.data:
            print(f"[create_job] Project {project_id} not found")
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
            print("[create_job] Foreign key violation")
            return {"error": "Invalid project_id. Project not found"}
        print(f"[create_job] Unexpected error: {e}")
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
        print(f"[get_jobs] Error: {e}")
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
        print(f"[get_job] Error: {e}")
        return None


async def update_job(job_id: str, update_data: Dict[str, Any], authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        if not update_data:
            print("[update_job] Missing update data")
            return {"error": "No update fields provided"}

        # Clean out None values
        update_payload = {k: v for k, v in update_data.items() if v is not None}
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

        print(f"[update_job] No job found with id {job_id}")
        return {"error": f"Job with id {job_id} not found"}

    except Exception as e:
        print(f"[update_job] Error: {e}")
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
        print(f"[delete_job] Error: {e}")
        return False
