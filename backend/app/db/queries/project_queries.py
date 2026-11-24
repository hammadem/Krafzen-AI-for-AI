import uuid
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.supabase_client import db
from app.models.project_model import ProjectCreate, ProjectUpdate
from app.utils.logger import logger


# CREATE PROJECT
async def create_project(project_data: ProjectCreate, user: dict[str, Any]) -> dict[str, Any] | None:
    if not user or "user_id" not in user:
        logger.warning("[create_project] Invalid user context")
        return None

    if not project_data.input_text.strip():
        raise HTTPException(status_code=422, detail="Project text cannot be blank")
    try:
        payload = {
            "user_id": user["user_id"],
            "input_text": project_data.input_text,
            **project_data.model_dump(exclude={"input_text"}, exclude_unset=True),
            "parsed_json": None,
            "created_at": datetime.now(UTC).isoformat(),
        }

        response = await run_in_threadpool(
            lambda: db.table("projects")
                .insert(payload)
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[create_project] Project created successfully", project_id=response.data[0]["id"]) 
            return response.data[0]

        logger.warning("[create_project] Insert failed")  
        return None

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[create_project] Unexpected error", error=str(e), exc_info=True)
        return None  

# GET ALL PROJECTS FOR THE LOGGED-IN USER
async def get_projects(user: dict[str, Any], page: int = 1, limit: int = 10, status: str | None = None, archived: bool = False, search: str | None = None, project_type: str | None = None, lifecycle_stage: str | None = None) -> list[dict[str, Any]]:  
    if not user or "user_id" not in user:
        logger.warning("[get_projects] Invalid user context")
        return []

    try:
        user_id = user["user_id"]  
        offset = (page - 1) * limit

        def build_query():
            query = db.table("projects").select("*").eq("user_id", user_id)
            # Archived projects are excluded from the active list, never lost.
            # The legacy 'status' parameter maps onto the real archived_at
            # lifecycle, not a nonexistent projects.status column.
            show_archived = archived or status == "archived"
            if show_archived:
                query = query.filter("archived_at", "not.is", "null")
            else:
                query = query.is_("archived_at", "null")
            if project_type:
                query = query.eq("project_type", project_type)
            if lifecycle_stage:
                query = query.eq("lifecycle_stage", lifecycle_stage)
            if search and search.strip():
                # Escape SQL LIKE wildcards; the value is a PostgREST filter, never SQL.
                term = search.strip().replace(chr(92), chr(92) * 2).replace("%", chr(92) + "%").replace("_", chr(92) + "_")
                # Quoted PostgREST filter values prevent commas/parentheses in names from becoming filter syntax.
                pattern = json.dumps("%" + term + "%", ensure_ascii=False)
                query = query.or_(",".join(f"{column}.ilike.{pattern}" for column in ("input_text", "title", "description")))
            return query.order("created_at", desc=True).order("id", desc=True).range(offset, offset + limit - 1).execute()
        response = await run_in_threadpool(build_query)

        if response is None:
            raise RuntimeError("Project storage returned no response")
        projects = response.data or []
        logger.debug(f"[get_projects] Retrieved {len(projects)} projects for user {user_id[:8]}...")
        return projects

    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as e:
        # An unavailable DB must NEVER appear as an empty project repository.
        # Otherwise users are prompted to recreate existing projects.
        logger.error("[get_projects] Error", user_id=user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(status_code=503, detail="Project storage temporarily unavailable") from e

# GET SINGLE PROJECT
async def get_project(project_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    if not user or "user_id" not in user:
        logger.warning("[get_project] Invalid user context")
        return None

    try:
        try:
            uuid.UUID(project_id)
        except (ValueError, TypeError):
            logger.warning("[get_project] Invalid UUID format", project_id=project_id)
            return None

        response = await run_in_threadpool(
            lambda: db.table("projects")
                .select("*")
                .eq("id", project_id)
                .maybe_single()
                .execute()
        )

        if not response or not response.data:
            logger.warning("[get_project] Project not found", project_id=project_id)
            return None

        project = response.data

        # enforce project ownership
        if project["user_id"] != user["user_id"]:
            logger.warning("[get_project] Unauthorized access attempt", project_id=project_id)
            raise HTTPException(status_code = 403, detail = {"error": "Access denied"})

        return project
    
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[get_project] Error", project_id=project_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=503, detail="Project storage temporarily unavailable") from e

# UPDATE PROJECT
async def update_project(project_id: str, update_data: ProjectUpdate, user: dict[str, Any]) -> dict[str, Any] | None:  
    if not user or "user_id" not in user:
        logger.warning("[update_project] Invalid user context")
        return None

    try:
        #UUID validation
        try:
            uuid.UUID(project_id)
        except (ValueError, TypeError):
            logger.warning("[update_project] Invalid UUID format", project_id=project_id)
            return None

        # fetch to verify ownership
        existing = await get_project(project_id, user)
        if not existing:
            logger.warning("[update_project] Unauthorized or not found", project_id=project_id)
            return None

        if existing.get("archived_at"):
            raise HTTPException(status_code=409, detail="Restore project before editing")
        payload = update_data.model_dump(exclude_unset=True)
        if not payload or ("input_text" in payload and (not isinstance(payload["input_text"], str) or not payload["input_text"].strip())):
            raise HTTPException(status_code=422, detail="Provide valid project information to update")
        payload["updated_at"] = datetime.now(UTC).isoformat()  
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .update(payload)
                .eq("id", project_id)
                .eq("user_id", user["user_id"])
                .is_("archived_at", "null")
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[update_project] Project updated successfully", project_id=project_id)  
            return response.data[0]

        logger.warning("[update_project] Update failed", project_id=project_id)  
        return None

    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[update_project] Error", project_id=project_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=503, detail="Project update unavailable") from e

# DELETE PROJECT
async def delete_project(project_id: str, user: dict[str, Any]) -> bool:  
    #User guard
    if not user or "user_id" not in user:
        logger.warning("[delete_project] Invalid user context")
        return False

    try:
        # UUID validation
        try:
            uuid.UUID(project_id)
        except (ValueError, TypeError):
            logger.warning("[delete_project] Invalid UUID format", project_id=project_id)
            return False

        # verify ownership
        existing = await get_project(project_id, user)
        if not existing:
            logger.warning("[delete_project] Unauthorized or not found", project_id=project_id)  
            return False

        response = await run_in_threadpool(
            lambda: db.table("projects")
                .delete()
                .eq("id", project_id)
                .eq("user_id", user["user_id"])
                .execute()
        )

        success = bool(response and response.data)
        if success:
            logger.info("[delete_project] Project deleted successfully", project_id=project_id)
        else:
            logger.warning("[delete_project] Delete failed", project_id=project_id)
        return success

    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as e:
        logger.error("[delete_project] Error", project_id=project_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=503, detail="Project deletion unavailable") from e

async def archive_project(project_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    """Soft-archive only a project owned by the current authenticated user."""
    if not user or not user.get("user_id"):
        return None
    existing = await get_project(project_id, user)
    if not existing:
        return None
    if existing.get("archived_at"):
        return existing
    now = datetime.now(UTC).isoformat()
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .update({"archived_at": now, "archived_by": user["user_id"], "updated_at": now})
                .eq("id", project_id)
                .eq("user_id", user["user_id"])
                .is_("archived_at", "null")
                .execute()
        )
        return response.data[0] if response and response.data else None
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.error("[archive_project] Failed", project_id=project_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Could not archive project") from exc


async def restore_project(project_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
    """Restore an owned archived project without deleting its files or history."""
    if not user or not user.get("user_id"):
        return None
    existing = await get_project(project_id, user)
    if not existing:
        return None
    if not existing.get("archived_at"):
        return existing
    now = datetime.now(UTC).isoformat()
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .update({
                    "archived_at": None, "archived_by": None,
                    "restored_at": now, "restored_by": user["user_id"],
                    "updated_at": now,
                })
                .eq("id", project_id)
                .eq("user_id", user["user_id"])
                .filter("archived_at", "not.is", "null")
                .execute()
        )
        return response.data[0] if response and response.data else None
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.error("[restore_project] Failed", project_id=project_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Could not restore project") from exc


async def update_generated_project_assets(
    project_id: str,
    *,
    user: dict[str, Any],
    image_url: str | None,
    dxf_url: str | None,
    dwg_url: str | None,
) -> dict[str, Any]:
    """Internal CAD generator only: persist actual uploaded artifact references.

    Never expose this function as a user-supplied PATCH model. The generating
    service has to verify ownership before spending work or uploading bytes.
    """
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("archived_at"):
        raise HTTPException(status_code=409, detail="Cannot modify archived project")
    assets = {
        key: value for key, value in (
            ("image_url", image_url),
            ("dxf_url", dxf_url),
            ("dwg_url", dwg_url),
        ) if value is not None
    }
    if not assets:
        raise HTTPException(status_code=422, detail="No generated asset to persist")
    assets["updated_at"] = datetime.now(UTC).isoformat()
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .update(assets)
                .eq("id", project_id)
                .eq("user_id", user["user_id"])
                .is_("archived_at", "null")
                .execute()
        )
        if response and response.data:
            return response.data[0]
        raise HTTPException(status_code=409, detail="Project changed while saving assets")
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.error("[update_generated_project_assets] Failed", project_id=project_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Could not persist generated CAD artifacts") from exc
