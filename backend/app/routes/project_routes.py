"""Project API routes (CRUD stub)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase_client import db
from app.db.queries.project_queries import create_project, get_projects
from app.models.project_model import ProjectCreate, ProjectOut

router = APIRouter()

@router.post("/projects/", response_model=ProjectOut)
async def create_project_route(project: ProjectCreate):
    # TODO: Auth dep for user_id
    result = await create_project(db, project)
    if not result:
        raise HTTPException(status_code=400, detail="Project creation failed")
    return result

@router.get("/projects/", response_model=List[ProjectOut])
async def list_projects(user_id: str):  # From auth dep later
    projects = await get_projects(db, user_id)
    return projects
