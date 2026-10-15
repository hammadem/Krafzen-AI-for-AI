
from fastapi import APIRouter, Depends, Query

from app.middlewares.auth import require_auth
from app.models.activity_model import ActivityEventResponse
from app.services.activity_service import get_project_activity, get_workspace_activity

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/", response_model=list[ActivityEventResponse])
async def list_activity(
    project_id: str = Query(...),
    limit: int = Query(default=50, le=100),
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
    limit: int = Query(default=50, le=100),
    user=Depends(require_auth),
):
    return await get_workspace_activity(workspace_id=workspace_id, user_id=user["user_id"], limit=limit)