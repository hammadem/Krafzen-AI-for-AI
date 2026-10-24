import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.services.activity_service import record_audit_event
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

        path = file_data.get("path")
        payload = {
            "job_id": job_id,
            "project_id": owned_project_id,
            "bucket": file_data.get("bucket", "krafzen-files"),
            "path": path,
            "file_type": file_data.get("file_type", "dxf"),
            "mime_type": file_data.get("mime_type"),
            "size_bytes": file_data.get("size_bytes"),
            "name": file_data.get("name") or (path.rsplit("/", 1)[-1] if path else None),
            "version": file_data.get("version", 1),
        }

        response = await run_in_threadpool(
            lambda: db.table("files")
            .insert(payload)
            .execute()
            )

        if response and response.data:
            created_file = response.data[0]
            await _record_file_activity("file.uploaded", created_file, user["user_id"])
            if created_file.get("version", 1) > 1:
                await _record_file_activity(
                    "file.version_created", created_file, user["user_id"]
                )
            await _record_revision_activity(
                "revision.created", created_file, user["user_id"]
            )
            logger.info("[create_file] File created successfully", file_id=created_file["id"])
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
                .is_("archived_at", "null")
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
            updated_file = response.data[0]
            old_name = file.get("name") or _file_name(file)
            new_name = updated_file.get("name") or _file_name(updated_file)
            name_changed = old_name != new_name
            if name_changed:
                await _record_file_activity(
                    "file.renamed",
                    updated_file,
                    user["user_id"],
                    old_name=old_name,
                    new_name=new_name,
                )
            changed_fields = sorted(
                field
                for field in payload
                if field != "name" and file.get(field) != updated_file.get(field)
            )
            if changed_fields:
                await _record_file_activity(
                    "file.updated",
                    updated_file,
                    user["user_id"],
                    changed_fields=changed_fields,
                )
            logger.info("[update_file] File updated successfully", file_id=file_id)
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

        response = await run_in_threadpool(
            lambda: db.table("files")
                .delete()
                .eq("id", file_id)
                .execute()
        )
        success = bool(response and hasattr(response, "data") and response.data)
        if success:
            logger.info("[delete_file] File deleted successfully", file_id=file_id) 
            await _record_file_activity("file.deleted", file, user["user_id"])
        else:
            logger.warning("[delete_file] Delete failed", file_id=file_id)
        return success
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[delete_file] Error", file_id=file_id, error=str(e), exc_info=True)
        return False


async def archive_file(file_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    file = await get_file(file_id, user)
    if not file:
        return None
    if file.get("archived_at"):
        return file

    archived_at = datetime.now(UTC).isoformat()
    response = await run_in_threadpool(
        lambda: db.table("files")
            .update({"archived_at": archived_at})
            .eq("id", file_id)
            .execute()
    )
    if not response or not response.data:
        return None

    archived_file = response.data[0]
    await _record_file_activity("file.archived", archived_file, user["user_id"])
    return archived_file


async def restore_file(file_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    file = await get_file(file_id, user)
    if not file:
        return None
    if not file.get("archived_at"):
        return file

    response = await run_in_threadpool(
        lambda: db.table("files")
            .update({"archived_at": None})
            .eq("id", file_id)
            .execute()
    )
    if not response or not response.data:
        return None

    restored_file = response.data[0]
    await _record_file_activity("file.restored", restored_file, user["user_id"])
    await _record_revision_activity(
        "revision.restored", restored_file, user["user_id"]
    )
    return restored_file


async def set_revision_approval(
    file_id: str,
    approval_state: str,
    user: dict[str, Any],
) -> dict[str, Any] | None:
    if approval_state not in {"approved", "rejected"}:
        raise ValueError("Revision approval state must be approved or rejected")

    file = await get_file(file_id, user)
    if not file:
        return None
    if file.get("approval_state") == approval_state:
        return file
    if not file.get("reviewed_by"):
        raise HTTPException(
            status_code=409,
            detail={"error": "The revision must be reviewed before a decision"},
        )
    if file.get("approval_state", "pending_review") != "pending_review":
        raise HTTPException(
            status_code=409,
            detail={"error": "The revision already has a final decision"},
        )

    response = await run_in_threadpool(
        lambda: db.table("files")
            .update({
                "approval_state": approval_state,
            })
            .eq("id", file_id)
            .eq("approval_state", "pending_review")
            .execute()
    )
    if not response or not response.data:
        return None

    updated_file = response.data[0]
    action = "revision.approved" if approval_state == "approved" else "revision.rejected"
    await _record_revision_activity(action, updated_file, user["user_id"])
    return updated_file


async def mark_revision_reviewed(
    file_id: str,
    user: dict[str, Any],
) -> dict[str, Any] | None:
    file = await get_file(file_id, user)
    if not file:
        return None
    if file.get("approval_state", "pending_review") != "pending_review":
        raise HTTPException(
            status_code=409,
            detail={"error": "Only pending revisions can be reviewed"},
        )
    if file.get("reviewed_by"):
        return file

    reviewed_at = datetime.now(UTC).isoformat()
    response = await run_in_threadpool(
        lambda: db.table("files")
            .update({
                "reviewed_by": user["user_id"],
                "reviewed_at": reviewed_at,
            })
            .eq("id", file_id)
            .eq("approval_state", "pending_review")
            .is_("reviewed_by", "null")
            .execute()
    )
    if not response or not response.data:
        raise HTTPException(
            status_code=409,
            detail={"error": "The revision was reviewed by another member"},
        )

    reviewed_file = response.data[0]
    await _record_revision_activity(
        "revision.reviewed",
        reviewed_file,
        user["user_id"],
    )
    return reviewed_file


async def _record_file_activity(
    action: str,
    file: dict[str, Any],
    actor_user_id: str,
    **details: Any,
) -> None:
    project_id = file.get("project_id")
    metadata: dict[str, Any] = {
        "file_id": file["id"],
        "file_name": _file_name(file),
        "file_type": file.get("file_type"),
        "version": file.get("version", 1),
        "project_id": project_id,
        "user_id": actor_user_id,
    }
    metadata.update({key: value for key, value in details.items() if value is not None})
    try:
        await record_audit_event(
            action=action,
            entity_type="file",
            entity_id=file["id"],
            actor_user_id=actor_user_id,
            project_id=project_id,
            file_id=file["id"],
            legacy_job_id=str(file["job_id"]) if file.get("job_id") else None,
            metadata=metadata,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"File state changed but {action} audit event could not be recorded",
                "entity_id": file["id"],
            },
        ) from error


async def _record_revision_activity(
    action: str,
    file: dict[str, Any],
    actor_user_id: str,
) -> None:
    metadata = {
        "revision_id": file["id"],
        "file_id": file["id"],
        "version": file.get("version", 1),
        "approval_state": file.get("approval_state", "pending_review"),
    }
    if action == "revision.reviewed":
        metadata["reviewed_by"] = actor_user_id
    elif action == "revision.approved":
        metadata["reviewed_by"] = file.get("reviewed_by")
        metadata["approved_by"] = actor_user_id
    elif action == "revision.rejected":
        metadata["reviewed_by"] = file.get("reviewed_by")
        metadata["decision_by"] = actor_user_id

    try:
        await record_audit_event(
            action=action,
            entity_type="revision",
            entity_id=file["id"],
            actor_user_id=actor_user_id,
            project_id=file.get("project_id"),
            legacy_job_id=str(file["job_id"]) if file.get("job_id") else None,
            file_id=file["id"],
            metadata=metadata,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Revision state changed but {action} audit event could not be recorded",
                "entity_id": file["id"],
            },
        ) from error


def _file_name(file: dict[str, Any]) -> str | None:
    name = file.get("name")
    if name:
        return name
    path = file.get("path")
    return path.rsplit("/", 1)[-1] if path else None
    
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
            artifact = res.data[0]
            source_file_id = file_data.get("source_file_id")
            event_file = {
                **artifact,
                "id": source_file_id or artifact["id"],
                "name": file_data.get("source_file_name") or artifact.get("name"),
            }
            await _record_file_activity(
                "file.exported",
                event_file,
                user_id,
                export_format=artifact.get("file_type"),
                artifact_file_id=artifact["id"],
            )
            logger.info("[create_artifact_file] Artifact file created", file_id=artifact["id"])
            return artifact

        return None
    except Exception as e:
        logger.error("[create_artifact_file] Error", error=str(e), exc_info=True)
        return None
