from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.models.project_model import ProjectCreate, ProjectUpdate


# CREATE
async def create_project(project_data: ProjectCreate, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        # Extract the Bearer token
        token = authorization.split(" ")[1]

        payload = {
            "user_id": project_data.user_id,
            "input_text": project_data.input_text,
            "parsed_json": None,
            "dxf_url": None,
        }

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .insert(payload)
            .headers({"Authorization": f"Bearer {token}"})
            .execute()
        )

        return response.data[0] if response.data else None

    except Exception as e:
        print(f"Create project error: {e}")
        return None


# READ
async def get_projects(user_id: str, authorization: str) -> List[Dict[str, Any]]:
    try:
        token = authorization.split(" ")[1]

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("*")
            .eq("user_id", user_id)
            .headers({"Authorization": f"Bearer {token}"})
            .execute()
        )

        return response.data

    except Exception as e:
        print(f"List projects error: {e}")
        return []


# GET ONE
async def get_project(project_id: str, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        token = authorization.split(" ")[1]

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("*")
            .eq("id", project_id)
            .single()
            .headers({"Authorization": f"Bearer {token}"})
            .execute()
        )

        return response.data

    except Exception as e:
        print(f"Get project error: {e}")
        return None


# UPDATE
async def update_project(project_id: str, update_data: ProjectUpdate, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        token = authorization.split(" ")[1]

        payload = update_data.dict(exclude_unset=True)
        payload["updated_at"] = datetime.utcnow()

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .update(payload)
            .eq("id", project_id)
            .headers({"Authorization": f"Bearer {token}"})
            .execute()
        )

        return response.data[0] if response.data else None

    except Exception as e:
        print(f"Update project error: {e}")
        return None


# DELETE
async def delete_project(project_id: str, authorization: str) -> bool:
    try:
        token = authorization.split(" ")[1]

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .delete()
            .eq("id", project_id)
            .headers({"Authorization": f"Bearer {token}"})
            .execute()
        )

        return bool(response.data)

    except Exception as e:
        print(f"Delete project error: {e}")
        return False
