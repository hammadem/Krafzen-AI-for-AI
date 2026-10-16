import uuid
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.services.activity_service import record_file_event
from app.utils.logger import logger


# Resolve a job's project only when it belongs to the authenticated user.
async def _get_owned_job_project_id(job_id: str, user_id: str) -> str | None:
    try:
        job_res = await run_in_threadpool(
            lambda: db.table("jobs")
                .select("project_id")
                .eq("id", job_id)
                .maybe_single()
                .execute()
        )

        if not job_res or not job_res.data:
            logger.warning("[_user_owns_job] Job not found", job_id=job_id)
            return None

        project_id = job_res.data["project_id"]

        proj_res = await run_in_threadpool(
            lambda: db.table("projects")
                .select("user_id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
        )

        if not proj_res or not proj_res.data:
            logger.warning("[_user_owns_job] Project not found", project_id=project_id)  
            return None

        owns = proj_res.data["user_id"] == user_id
        if not owns:
            logger.warning("[_user_owns_job] Unauthorized access attempt", job_id=job_id, user_id=user_id[:8] + "...") 
            return None
        return str(project_id)

    except Exception as e:  
        logger.error("[_user_owns_job] Query error", job_id=job_id, error=str(e), exc_info=True)
        return None


async def _user_owns_job(job_id: str, user_id: str) -> bool:
    return await _get_owned_job_project_id(job_id, user_id) is not None


def _file_name(file_data: dict[str, Any]) -> str:
    name = file_data.get("name")
    if name and str(name).strip():
        return str(name)
    return str(file_data.get("path") or "file").rstrip("/").split("/")[-1] or "file"

# CREATE FILE (saves metadata to DB, path must come from whoever uploaded to Storage)
async def create_file(file_data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any] | None:
    if not user or "user_id" not in user:
        logger.warning("[create_file] Invalid user context")
        return {"error": "Invalid user context"}

    try:
        job_id = file_data.get("job_id")
        project_id = file_data.get("project_id")

        if not job_id :
            return {"error": "job_id is required"}
        
        try:
            uuid.UUID(job_id)
            if project_id:
                uuid.UUID(project_id)
        except (ValueError, TypeError):
            return {"error": "Invalid job_id or project_id format"}
        
        owned_project_id = await _get_owned_job_project_id(job_id, user["user_id"])
        if not owned_project_id:
            raise HTTPException(status_code=403, detail={"error": "Access denied"})
        if project_id and project_id != owned_project_id:
            raise HTTPException(status_code=400, detail={"error": "project_id does not match job"})

        payload = {
            "job_id": job_id,
            "project_id": owned_project_id,
            "bucket": file_data.get("bucket", "krafzen-files"),
            "path": file_data.get("path"),
            "file_type": file_data.get("file_type", "dxf"),
            "mime_type": file_data.get("mime_type"),
            "size_bytes": file_data.get("size_bytes"),
            "name": file_data.get("name"),
        }

        response = await run_in_threadpool(
            lambda: db.table("files")
            .insert(payload)
            .execute()
            )

        if response and response.data:
            created_file = response.data[0]
            logger.info("[create_file] File created successfully", file_id=created_file["id"])
            try:
                await record_file_event(
                    event_name="file.uploaded",
                    file_id=str(created_file["id"]),
                    project_id=owned_project_id,
                    job_id=job_id,
                    actor_user_id=user["user_id"],
                    metadata={"file_name": _file_name(created_file)},
                    message=f"Uploaded {_file_name(created_file)}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={"error": "File was created but its activity event could not be recorded"},
                ) from e
            return created_file
        
        logger.warning("[create_file] Insert failed")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[create_file] Unexpected error", error=str(e), exc_info=True)
        return {"error": "Unexpected server error"}



# LIST FILES
async def get_files(job_id: str, user: dict[str, Any]) -> list[dict[str, Any]]:
    if not user or "user_id" not in user:
        logger.warning("[get_files] Invalid user context")
        return []

    try:
        try:
            uuid.UUID(job_id)
        except (ValueError, TypeError):
            logger.warning("[get_files] Invalid UUID format", job_id=job_id)
            return []

        owns = await _user_owns_job(job_id, user["user_id"])
        if not owns:
            logger.warning("[get_files] Unauthorized access attempt", job_id=job_id)
            return []

        response = await run_in_threadpool(
            lambda: db.table("files")
                .select("*")
                .eq("job_id", job_id)
                .execute()
        )

        files = response.data if response and response.data else []
        logger.debug(f"[get_files] Retrieved {len(files)} files", job_id=job_id)
        return files

    except Exception as e:
        logger.error("[get_files] Error", job_id=job_id, error=str(e), exc_info=True)
        return []

# GET SINGLE FILE
async def get_file(file_id: str, user: dict[str, Any]) -> dict[str, Any] | None:  
    if not user or "user_id" not in user:
        logger.warning("[get_file] Invalid user context")
        return None

    try:
        try:
            uuid.UUID(file_id)
        except (ValueError, TypeError):
            logger.warning("[get_file] Invalid UUID format", file_id=file_id)
            return None

        res = await run_in_threadpool(
            lambda: db.table("files")
                .select("*")
                .eq("id", file_id)
                .maybe_single()
                .execute()
        )

        if not res or not res.data:
            logger.warning("[get_file] File not found", file_id=file_id)
            return None

        file_data = res.data  
        owned_project_id = await _get_owned_job_project_id(file_data["job_id"], user["user_id"])
        if not owned_project_id:
            logger.warning("[get_file] Unauthorized access attempt", file_id=file_id) 
            raise HTTPException(status_code=403, detail={"error": "Access denied"})

        file_data["project_id"] = owned_project_id
        return file_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return None

# UPDATE FILE
async def update_file(file_id: str, update_data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any] | None:  
    if not user or "user_id" not in user:
        logger.warning("[update_file] Invalid user context")
        return {"error": "Invalid user context"}

    try:
        try:
            uuid.UUID(file_id)
        except (ValueError, TypeError):
            logger.warning("[update_file] Invalid UUID format", file_id=file_id)
            return {"error": f"Invalid file_id format: {file_id}. Must be a valid UUID."}

        file = await get_file(file_id, user)
        if not file:
            return {"error": "Unauthorized or file not found"}

        payload = {k: v for k, v in update_data.items() if v is not None}
        #payload["updated_at"] = datetime.now(timezone.utc).isoformat()  no such column in the db table Files

        if not payload:  
            return {"error": "No valid update fields provided"}

        response = await run_in_threadpool(
            lambda: db.table("files")
                .update(payload)
                .eq("id", file_id)
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[update_file] File updated successfully", file_id=file_id) 
            updated_file = response.data[0]
            if "name" in payload or "path" in payload:
                try:
                    project_id = (
                        updated_file.get("project_id")
                        or file.get("project_id")
                        or await _get_owned_job_project_id(file["job_id"], user["user_id"])
                    )
                    await record_file_event(
                        event_name="file.renamed",
                        file_id=file_id,
                        project_id=str(project_id or ""),
                        job_id=str(updated_file["job_id"]),
                        actor_user_id=user["user_id"],
                        metadata={
                            "previous_name": _file_name(file),
                            "file_name": _file_name(updated_file),
                        },
                        message=f"Renamed {_file_name(file)} to {_file_name(updated_file)}",
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail={"error": "File was updated but its activity event could not be recorded"},
                    ) from e
            return updated_file

        logger.warning("[update_file] Update failed", file_id=file_id) 
        return {"error": f"File with id {file_id} not found"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[update_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return {"error": "Unexpected server error"}

# DELETE FILE
async def delete_file(file_id: str, user: dict[str, Any]) -> bool:  
    if not user or "user_id" not in user:
        logger.warning("[delete_file] Invalid user context")
        return False

    try:
        try:
            uuid.UUID(file_id)
        except (ValueError, TypeError):
            logger.warning("[delete_file] Invalid UUID format", file_id=file_id)
            return False

        file = await get_file(file_id, user)
        if not file:
            logger.warning("[delete_file] File not authorized or not found", file_id=file_id) 
            return False
        
        # delete from Storage
        try:
            await run_in_threadpool(
                lambda: db.storage.from_(file["bucket"]).remove([file["path"]]))
        except Exception as e:
            logger.error("[delete_file] Storage delete failed", file_id=file_id, error=str(e))
            raise HTTPException(status_code=500, detail={"error": "Failed to delete file from storage"})

        # delete from DB only when storage delete succeeded
        response = await run_in_threadpool(
            lambda: db.table("files")
                .delete()
                .eq("id", file_id)
                .execute()
        )

        success = bool(response and hasattr(response, "data") and response.data)
        if success:
            logger.info("[delete_file] File deleted successfully", file_id=file_id) 
            try:
                project_id = (
                    file.get("project_id")
                    or await _get_owned_job_project_id(file["job_id"], user["user_id"])
                )
                await record_file_event(
                    event_name="file.deleted",
                    file_id=file_id,
                    project_id=str(project_id or ""),
                    job_id=str(file["job_id"]),
                    actor_user_id=user["user_id"],
                    metadata={"file_name": _file_name(file)},
                    message=f"Deleted {_file_name(file)}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={"error": "File was deleted but its activity event could not be recorded"},
                ) from e
        else:
            logger.warning("[delete_file] Delete failed", file_id=file_id)
        return success
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[delete_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return False
    
# GET SIGNED URL
async def get_signed_url(file_id: str, user: dict[str, Any]) -> str | None:
    file = await get_file(file_id, user)
    if not file:
        return None
    
    try:
        res = await run_in_threadpool(
            lambda: db.storage.from_(file["bucket"]).create_signed_url(file["path"], 3600)
        )
        return res.get("signedURL") or res.get("signed_url")
    except Exception as e:
        logger.error("[get_signed_url] Error", file_id=file_id, error=str(e), exc_info=True)
        return None
    
    
# CREATE ARTIFACT FILE (called after Tazwar uploads export to storage)
async def create_artifact_file(file_data: dict[str, Any], user_id: str) -> dict[str, Any] | None:
    try:
        payload = {
            "bucket": file_data.get("bucket", "dxf-files"),
            "path": file_data.get("path"),
            "file_type": file_data.get("file_type", "dxf"),
            "mime_type": file_data.get("mime_type"),
            "size_bytes": file_data.get("size_bytes"),
            "name": file_data.get("name"),
            "project_id": file_data.get("project_id"),
            "job_id": file_data.get("job_id"),
        }

        res = await run_in_threadpool(
            lambda: db.table("files")
                .insert(payload)
                .execute()
        )

        if res and res.data:
            logger.info("[create_artifact_file] Artifact file created", file_id=res.data[0]["id"])
            return res.data[0]

        return None
    except Exception as e:
        logger.error("[create_artifact_file] Error", error=str(e), exc_info=True)
        return None
