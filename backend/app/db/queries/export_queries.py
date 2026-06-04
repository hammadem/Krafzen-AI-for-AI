from app.utils.validators import _user_owns_project, _valid_uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger

VALID_STATUSES = ("queued", "processing", "validating","completed", "failed", "requires_review")

#CREATE EXPORT 
async def create_export(job_id: str, project_id:str, format: str, user_id: str)-> Optional[Dict[str,Any]]:
    if not _valid_uuid(job_id) or not _valid_uuid(project_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid ID format"})
    
    try:
        owns = await _user_owns_project(project_id, user_id)
        if not owns:
            raise HTTPException(status_code=403, detail={"error": "Access denied"})

        res = await run_in_threadpool(
            lambda: db.table("exports")
            .insert({
                    "job_id": job_id,
                    "project_id": project_id,
                    "requested_by": user_id,
                    "format": format,
                    "status": "queued"
                })
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=500, detail={"error": "Failed to create export"})

        return res.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[create_export] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    
#GET EXPORT
async def get_export(export_id: str, user_id: str)-> Optional[Dict[str,Any]]:
    if not _valid_uuid(export_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid export_id"})
    
    try:
        res = await run_in_threadpool(
            lambda: db.table("exports")
                .select("*")
                .eq("id", export_id)
                .maybe_single()
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "Export not found"})

        if res.data["requested_by"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Access denied"})

        return res.data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_export] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    

# LIST EXPORTS FOR PROJECT
async def get_project_exports(project_id: str,user_id: str)->List[Dict[str, Any]]:
    if not _valid_uuid(project_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid project_id"})

    try:
        owns = await _user_owns_project(project_id, user_id)
        if not owns:
            raise HTTPException(status_code=403, detail={"error": "Access denied"})

        res = await run_in_threadpool(
            lambda: db.table("exports")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .execute()
        )

        return res.data if res and res.data else []

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_project_exports] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    
    
# UPDATE EXPORT STATUS
async def update_export_status(
    export_id: str,
    update_data: Dict[str, Any],
    user_id: str
) -> Optional[Dict[str, Any]]:
    if not _valid_uuid(export_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid export_id"})

    status = update_data.get("status")
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail={"error": f"Invalid status: {status}"})

    try:
        await get_export(export_id, user_id)

        payload = {k: v for k, v in update_data.items() if v is not None}
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        res = await run_in_threadpool(
            lambda: db.table("exports")
                .update(payload)
                .eq("id", export_id)
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "Export not found"})

        return res.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[update_export_status] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})