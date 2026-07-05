from fastapi import APIRouter, Depends, Query
from app.middlewares.auth import require_auth
from app.services.notification_service import get_notifications, mark_as_read

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def list_notifications(
    unread_only: bool = Query(default=False),
    user=Depends(require_auth),
):
    return await get_notifications(user["user_id"], unread_only=unread_only)


@router.patch("/{notification_id}/read")
async def read_notification(notification_id: str, user=Depends(require_auth)):
    success = await mark_as_read(notification_id, user["user_id"])
    return {"success": success}