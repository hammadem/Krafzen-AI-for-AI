from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List
from app.db.queries.project_queries import (
    create_project as create_project_query,
    get_projects,
    get_project,
    update_project,
    delete_project
)
from app.models.project_model import ProjectCreate, ProjectUpdate, ProjectOut
from app.core.config import settings

router = APIRouter(prefix="/projects", tags=["Projects"])



# CREATE PROJECT
@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project_route(
    project: ProjectCreate,
    authorization: str = Header(None)
):
    result = await create_project_query(project, authorization)
    if not result:
        raise HTTPException(status_code=400, detail="Project creation failed")
    return result


# LIST PROJECTS FOR USER
@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    user_id: str = Query(..., description="User ID (UUID)"),
    authorization: str = Header(None)
):
    projects = await get_projects(user_id, authorization)
    return projects


# GET SINGLE PROJECT
@router.get("/{project_id}", response_model=ProjectOut)
async def get_project_route(
    project_id: str,
    authorization: str = Header(None)
):
    project = await get_project(project_id, authorization)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# UPDATE PROJECT
@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project_route(
    project_id: str,
    update_data: ProjectUpdate,
    authorization: str = Header(None)
):
    updated = await update_project(project_id, update_data, authorization)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found or no changes applied")  
    return updated


# DELETE PROJECT
@router.delete("/{project_id}")
async def delete_project_route(
    project_id: str,
    authorization: str = Header(None)
):
    deleted = await delete_project(project_id, authorization)
    if not deleted:
        raise HTTPException(status_code=400, detail="Delete failed")
    return {"message": "Project deleted successfully"}


# DEBUG ENV
@router.get("/debug/env")
async def debug_env():
    return {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SERVICE_ROLE_KEY": settings.SUPABASE_SERVICE_ROLE_KEY[:8] + "...",
        "ANON": settings.SUPABASE_ANON_KEY[:8] + "..."
    }
