from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middlewares.auth import require_auth
from app.db.supabase_client import db
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, StrictBool
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
class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    imports: StrictBool = True
    exports: StrictBool = True
    reviews: StrictBool = True
    field: StrictBool = True
    collaboration: StrictBool = True
    validation: StrictBool = True


@router.get("/preferences",response_model=Preferences)
async def read_preferences(user=Depends(require_auth)):
    try:
        result=await run_in_threadpool(lambda:db.table("notification_preferences").select("imports,exports,reviews,field,collaboration,validation").eq("user_id",user["user_id"]).limit(1).execute())
        if result is None or result.data is None:
            raise RuntimeError("Preferences unavailable")
        return result.data[0] if result.data else Preferences()
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Notification preferences unavailable") from exc


@router.put("/preferences",response_model=Preferences)
async def save_preferences(body:Preferences,user=Depends(require_auth)):
    # No identity supplied by client and no direct browser table privileges.
    try:
        result=await run_in_threadpool(lambda:db.table("notification_preferences").upsert({"user_id":user["user_id"],**body.model_dump()},on_conflict="user_id").execute())
        if not result or not result.data:
            raise RuntimeError("Preferences not saved")
        return {k:result.data[0][k] for k in Preferences.model_fields}
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Notification preferences could not be saved") from exc


@router.post("/read-all")
async def read_all(user=Depends(require_auth)):
    try:
        result=await run_in_threadpool(lambda:db.table("notifications").update({"is_read":True},returning="minimal").eq("user_id",user["user_id"]).eq("is_read",False).execute())
        if result is None:
            raise RuntimeError("Notification update unavailable")
        return {"success":True}
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Notification update unavailable") from exc
