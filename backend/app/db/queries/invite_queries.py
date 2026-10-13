from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.db.queries.workspace_queries import get_workspace
from app.db.supabase_client import db
from app.utils.logger import logger
from app.utils.validators import _valid_uuid


#CREATE INVITE
async def create_invite(workspace_id: str, email: str, role: str, user_id: str) -> dict[str, Any] | None:
    if not _valid_uuid(workspace_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid workspace_id"})
    if role not in ("admin", "member", "viewer"):
       raise HTTPException(status_code=400, detail={"error": "Invalid role"})

    try:
        workspace = await get_workspace(workspace_id, user_id)

        if workspace["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only owner can invite members"})

        # duplicate check
        existing = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .select("id, status")
                .eq("workspace_id", workspace_id)
                .eq("email", email)
                .maybe_single()
                .execute()
        )

        if existing and existing.data:
            if existing.data["status"] == "pending":
                raise HTTPException(status_code=409, detail={"error": "Invite already sent to this email"})
            
        res = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .insert({
                    "workspace_id": workspace_id,
                    "email": email,
                    "invited_by": user_id,
                    "role": role
                })
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=500, detail={"error": "Failed to create invite"})

        return res.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[create_invite] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    

#REVOKE INVITE
async def revoke_invite(invite_id: str ,user_id: str) -> bool:
    if not _valid_uuid(invite_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid invite_id"})
    
    try: 
        invite = await run_in_threadpool(
            lambda: db.table("workspace_invites")
            .select("*")
            .eq("id", invite_id)
            .maybe_single()
            .execute()
        )

        if not invite or not invite.data:
            raise HTTPException(status_code=404, detail={"error": "Invite not found"})

        if invite.data["invited_by"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only the inviter can revoke this invite"})

        if invite.data["status"] != "pending":
            raise HTTPException(status_code=400, detail={"error": "Only pending invites can be revoked"})
        
        res = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .update({"status": "revoked"})
                .eq("id", invite_id)
                .execute()
        )

        return bool(res and res.data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[revoke_invite] Error", error=str(e), exc_info=True)
        return False
    

#VALIDATE INVITE
async def validate_invite(token: str) -> dict[str, Any]:
    if not _valid_uuid(token):
        return {"valid": False, "message": "Invalid token format"}

    try:
        res = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .select("*")
                .eq("token", token)
                .maybe_single()
                .execute()
        )

        if not res or not res.data:
            return {"valid": False, "message": "Invite not found"}

        invite = res.data

        if invite["status"] == "revoked":
            return {"valid": False, "message": "Invite has been revoked"}

        if invite["status"] == "accepted":
            return {"valid": False, "message": "Invite already accepted"}

        expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
        if datetime.now(UTC) > expires_at:
            await run_in_threadpool(
                lambda: db.table("workspace_invites")
                    .update({"status": "expired"})
                    .eq("id", invite["id"])
                    .execute()
            )
            return {"valid": False, "message": "Invite has expired"}

        return {
            "valid": True,
            "workspace_id": invite["workspace_id"],
            "email": invite["email"],
            "role": invite["role"],
            "message": "Invite is valid"
        }

    except Exception as e:
        logger.error("[validate_invite] Error", error=str(e), exc_info=True)
        return {"valid": False, "message": "Server error"}
        

#LIST ALL INVITES 
async def get_workspace_invites(workspace_id: str,user_id: str) -> list[dict[str, Any]]:
    if not _valid_uuid(workspace_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid workspace_id"})

    try:
        workspace = await get_workspace(workspace_id, user_id)

        if workspace["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only owner can view invites"})

        res = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .select("*")
                .eq("workspace_id", workspace_id)
                .order("created_at", desc=True)
                .execute()
        )

        return res.data if res and res.data else []

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_workspace_invites] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})