from fastapi import APIRouter, Depends, Query
from app.middlewares.auth import require_auth
from app.services.activity_service import get_project_activity

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/")
async def list_activity(
    project_id: str = Query(...),
    limit: int = Query(default=50, le=100),
    user=Depends(require_auth),
):
    """
    Return recent activity events for a project.
    Sunny's frontend polls this for the live activity feed.
    """
    return await get_project_activity(project_id, limit=limit)