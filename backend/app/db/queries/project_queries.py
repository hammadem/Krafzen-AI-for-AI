from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.models.project_model import ProjectCreate, ProjectUpdate


# CREATE
async def create_project(project_data: ProjectCreate, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        token = None
        if authorization:
            parts = authorization.split(" ")
            if len(parts) == 2:
                token = parts[1]

        payload = {
            "user_id": project_data.user_id,
            "input_text": project_data.input_text,
            "parsed_json": None,
            "dxf_url": None,
        }

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .insert(payload)
            .execute()
        )

        return response.data[0] if response and hasattr(response, 'data') and response.data else None

    except Exception as e:
        print(f"Create project error: {e}")
        return None


# READ
async def get_projects(user_id: str, authorization: str) -> List[Dict[str, Any]]:
    try:
        print(f"DEBUG: Fetching projects for user_id='{user_id}'")

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        print(f"DEBUG response.data={response.data}")
        return response.data if response and hasattr(response, 'data') and response.data else []

    except Exception as e:
        print(f"List projects error: {e}")
        return []



# GET ONE
async def get_project(project_id: str, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        token = None
        if authorization:
            parts = authorization.split(" ")
            if len(parts) == 2:
                token = parts[1]

        # Query Supabase
        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("*")
            .eq("id", project_id)
            .maybe_single()
            .execute()
        )
        print(f"DEBUG get_project: id={project_id}, response={response}")
        if not response or not getattr(response, "data", None):
            print("DEBUG: No project found with this ID.")
            return None

        return response.data if response and hasattr(response, 'data') and response.data else None

    except Exception as e:
        print(f"Get project error: {e}")
        return None



# UPDATE
async def update_project(project_id: str, update_data: ProjectUpdate, authorization: str) -> Optional[Dict[str, Any]]:
    try:
        payload = update_data.model_dump(exclude_unset=True)
        payload["updated_at"] = datetime.utcnow().isoformat() 
        print(f"DEBUG: project_id='{project_id}', payload={payload}")

        response = await run_in_threadpool(
            lambda: db.table("projects")
            .update(payload)
            .eq("id", project_id)
            .execute()
        )
        print(f"DEBUG: response.data={response.data}, len={len(response.data)}")

        return response.data[0] if response and hasattr(response, 'data') and response.data else None
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
            .execute()
        )

        return bool(response and hasattr(response, 'data') and response.data)

    except Exception as e:
        print(f"Delete project error: {e}")
        return False