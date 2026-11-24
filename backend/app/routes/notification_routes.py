from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

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
async def read_notification(notification_id: UUID, user=Depends(require_auth)):
    if not await mark_as_read(str(notification_id), user["user_id"]):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}