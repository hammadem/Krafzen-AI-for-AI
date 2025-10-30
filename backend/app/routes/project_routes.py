from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List
from app.db.queries.project_queries import (
    create_project as create_project_query,
    get_projects,
)
from app.models.project_model import ProjectCreate, ProjectOut
from app.core.config import settings


router = APIRouter(prefix="/projects", tags=["projects"])

# Create Project
@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project_route(
    project: ProjectCreate,
    authorization: str = Header(None)
):
    """Create a new project for a user."""
    result = await create_project_query(project, authorization)
    if not result:
        raise HTTPException(status_code=400, detail="Project creation failed")
    return result


# List Projects for a User
@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    user_id: str = Query(..., description="User ID (UUID)"),
    authorization: str = Header(None)
):
    """List all projects belonging to a user."""
    projects = await get_projects(user_id, authorization)
    return projects

@router.get("/debug/env")
async def debug_env():
    return {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SERVICE_SERVICE_ROLE_KEY": settings.SUPABASE_SERVICE_ROLE_KEY[:8] + "...",
        "ANON": settings.SUPABASE_ANON_KEY[:8] + "..."
    }
