from typing import List, Dict, Any, Optional
from datetime import datetime, timezone  
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.utils.logger import logger
from app.models.project_model import ProjectCreate, ProjectUpdate
import uuid  

# CREATE PROJECT
async def create_project(project_data: ProjectCreate, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not user or "user_id" not in user:
        logger.warning("[create_project] Invalid user context")
        return None

    try:
        payload = {
            "user_id": user["user_id"],
            "input_text": project_data.input_text,
            "parsed_json": None,
            "image_url": None,
            "dxf_url": None,
            "dwg_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
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

    except Exception as e:
        logger.error("[create_project] Unexpected error", error=str(e), exc_info=True)
        return None  

# GET ALL PROJECTS FOR THE LOGGED-IN USER
async def get_projects(user: Dict[str, Any]) -> List[Dict[str, Any]]:  
    if not user or "user_id" not in user:
        logger.warning("[get_projects] Invalid user context")
        return []

    try:
        user_id = user["user_id"]  

        response = await run_in_threadpool(
            lambda: db.table("projects")
                .select("*")
                .eq("user_id", user_id)
                .execute()
        )

        projects = response.data if (response and response.data) else []
        logger.debug(f"[get_projects] Retrieved {len(projects)} projects for user {user_id[:8]}...")
        return projects

    except Exception as e:
        logger.error("[get_projects] Error", user_id=user["user_id"], error=str(e), exc_info=True)
        return []

# GET SINGLE PROJECT
async def get_project(project_id: str, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            return None

        return project

    except Exception as e:
        logger.error("[get_project] Error", project_id=project_id, error=str(e), exc_info=True)
        return None

# UPDATE PROJECT
async def update_project(project_id: str, update_data: ProjectUpdate, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:  
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

        payload = update_data.model_dump(exclude_unset=True)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()  #Timezone

        if not payload:  #Guard for empty updates
            logger.warning("[update_project] No fields to update", project_id=project_id)
            return existing  
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .update(payload)
                .eq("id", project_id)
                .execute()
        )

        if response and hasattr(response, "data") and response.data:
            logger.info("[update_project] Project updated successfully", project_id=project_id)  
            return response.data[0]

        logger.warning("[update_project] Update failed", project_id=project_id)  
        return None

    except Exception as e:
        logger.error("[update_project] Error", project_id=project_id, error=str(e), exc_info=True)
        return None

# DELETE PROJECT
async def delete_project(project_id: str, user: Dict[str, Any]) -> bool:  
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
                .execute()
        )

        success = bool(response and response.data)
        if success:
            logger.info("[delete_project] Project deleted successfully", project_id=project_id)
        else:
            logger.warning("[delete_project] Delete failed", project_id=project_id)
        return success

    except Exception as e:
        logger.error("[delete_project] Error", project_id=project_id, error=str(e), exc_info=True)
        return False