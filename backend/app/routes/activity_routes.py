from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.queries.file_queries import get_file
from app.middlewares.auth import require_auth
from app.models.activity_model import ActivityEventResponse
from app.services.activity_service import (
    get_file_activity,
    get_project_activity,
    get_workspace_activity,
)

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/", response_model=list[ActivityEventResponse])
async def list_activity(
    project_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(require_auth),
):
    return await get_project_activity(
        project_id=project_id,
        user_id=user["user_id"],
        limit=limit,
    )


@router.get("/workspace/{workspace_id}", response_model=list[ActivityEventResponse])
async def list_workspace_activity(
    workspace_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(require_auth),
):
    return await get_workspace_activity(workspace_id=workspace_id, user_id=user["user_id"], limit=limit)


@router.get("/files/{file_id}", response_model=list[ActivityEventResponse])
async def list_file_activity(
    file_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(require_auth),
):
    file = await get_file(file_id=file_id, user=user)
    if not file:
        raise HTTPException(status_code=404, detail={"error": "File not found"})
    return await get_file_activity(
        file_id=file_id,
        job_id=str(file["job_id"]),
        project_id=str(file["project_id"]),
        limit=limit,
    )