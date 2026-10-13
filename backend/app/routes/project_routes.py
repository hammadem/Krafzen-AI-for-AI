
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.queries.project_queries import create_project as create_project_query
from app.db.queries.project_queries import (
    delete_project,
    get_project,
    get_projects,
    update_project,
)
from app.middlewares.auth import require_auth
from app.models.project_model import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project_route(
    project: ProjectCreate,
    user: dict = Depends(require_auth)
):
    result = await create_project_query(project, user)
    if not result:
        raise HTTPException(status_code=400, detail={"error":"Project creation failed"})
    return result


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    user: dict = Depends(require_auth),
    page : int = Query(default=1, ge=1),
    limit: int = Query(default=10,ge=1,le=100),
    status: str | None = Query(default=None)
):
    projects = await get_projects(user, page = page, limit = limit, status=status)
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project_route(
    project_id: str,
    user: dict = Depends(require_auth)
):
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail={"error":"Project not found"})
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project_route(
    project_id: str,
    update_data: ProjectUpdate,
    user: dict = Depends(require_auth)
):
    updated = await update_project(project_id, update_data, user)
    if not updated:
        raise HTTPException(status_code=404, detail={"error":"Project not found or no changes applied"})
    return updated


@router.delete("/{project_id}")
async def delete_project_route(
    project_id: str,
    user: dict = Depends(require_auth)
):
    deleted = await delete_project(project_id, user)
    if not deleted:
        raise HTTPException(status_code=400, detail={"error":"Delete failed"})
    return {"message": "Project deleted successfully"}
