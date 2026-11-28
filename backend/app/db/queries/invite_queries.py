from datetime import UTC, datetime, timedelta
from uuid import uuid4
from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.queries.workspace_queries import get_workspace
from app.db.supabase_client import db
from app.services.activity_service import record_workspace_event
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

        # One row per workspace/email is enforced by the database. Reissue
        # revoked or expired invitations instead of inserting a duplicate row.
        existing = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .select("id, status, token, expires_at")
                .eq("workspace_id", workspace_id)
                .eq("email", email)
                .maybe_single()
                .execute()
        )
        current = existing.data if existing and existing.data else None
        now = datetime.now(UTC)
        if current:
            status = current["status"]
            expired_pending = status == "pending" and datetime.fromisoformat(current["expires_at"]) <= now
            if status == "pending" and not expired_pending:
                raise HTTPException(status_code=409, detail={"error": "Invite already sent to this email"})
            if status not in ("revoked", "expired") and not expired_pending:
                raise HTTPException(status_code=409, detail={"error": "Invitation has already been accepted"})
            res = await run_in_threadpool(
                lambda: db.table("workspace_invites")
                    .update({
                        "status": "pending",
                        "token": str(uuid4()),
                        "invited_by": user_id,
                        "role": role,
                        "created_at": now.isoformat(),
                        "expires_at": (now + timedelta(days=7)).isoformat(),
                    })
                    .eq("id", current["id"])
                    .eq("workspace_id", workspace_id)
                    .eq("status", status)
                    .eq("token", current["token"])
                    .execute()
            )
            if not res or not res.data:
                raise HTTPException(status_code=409, detail={"error": "Invitation changed; reload and try again"})
        else:
            try:
                res = await run_in_threadpool(
                    lambda: db.table("workspace_invites")
                        .insert({
                            "workspace_id": workspace_id,
                            "email": email,
                            "invited_by": user_id,
                            "role": role,
                        })
                        .execute()
                )
            except APIError as exc:
                if exc.code == "23505":
                    raise HTTPException(status_code=409, detail={"error": "Invitation already exists; reload and try again"}) from exc
                raise
            if not res or not res.data:
                raise HTTPException(status_code=500, detail={"error": "Failed to create invite"})

        invite = res.data[0]
        await record_workspace_event(
            event_name="team.member_invited",
            workspace_id=workspace_id,
            actor_user_id=user_id,
            metadata={
                "invite_id": invite["id"],
                "role": role,
            },
            message=f"Workspace invitation created with {role.title()} role.",
        )
        return invite
    
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[create_invite] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    

#REVOKE INVITE
async def revoke_invite(workspace_id: str, invite_id: str, user_id: str) -> bool:
    if not _valid_uuid(workspace_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid workspace_id"})
    if not _valid_uuid(invite_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid invite_id"})
    
    try: 
        invite = await run_in_threadpool(
            lambda: db.table("workspace_invites")
            .select("*")
            .eq("id", invite_id)
            .eq("workspace_id", workspace_id)
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
                .eq("workspace_id", workspace_id)
                .eq("invited_by", user_id)
                .eq("token", invite.data["token"])
                .eq("status", "pending")
                .execute()
        )

        if not res or not res.data:
            return False

        await record_workspace_event(
            event_name="permissions.access_revoked",
            workspace_id=invite.data["workspace_id"],
            actor_user_id=user_id,
            metadata={
                "invite_id": invite_id,
                "role": invite.data["role"],
                "access_scope": "pending_invitation",
            },
            message="A pending workspace invitation was revoked.",
        )
        return True
    
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[revoke_invite] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})


async def accept_invite(token: str, user_id: str) -> dict[str, Any]:
    """Accept an invitation for the authenticated user whose email matches it."""
    if not _valid_uuid(token):
        raise HTTPException(status_code=400, detail={"error": "Invalid token format"})

    try:
        invite_res = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .select("*")
                .eq("token", token)
                .maybe_single()
                .execute()
        )
        if not invite_res or not invite_res.data:
            raise HTTPException(status_code=404, detail={"error": "Invite not found"})

        invite = invite_res.data
        if invite["status"] != "pending":
            raise HTTPException(status_code=409, detail={"error": "Invite is not pending"})

        expires_at = datetime.fromisoformat(invite["expires_at"])
        if datetime.now(UTC) > expires_at:
            await run_in_threadpool(
                lambda: db.table("workspace_invites")
                    .update({"status": "expired"})
                    .eq("id", invite["id"])
                    .eq("token", token)
                    .eq("status", "pending")
                    .execute()
            )
            raise HTTPException(status_code=410, detail={"error": "Invite has expired"})

        auth_user_res = await run_in_threadpool(
            lambda: db.auth.admin.get_user_by_id(user_id)
        )
        auth_user = auth_user_res.user if auth_user_res else None
        user_email = auth_user.email if auth_user else None
        if not user_email or user_email.casefold() != invite["email"].casefold():
            raise HTTPException(status_code=403, detail={"error": "Invite email does not match authenticated user"})

        existing_member = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("user_id")
                .eq("workspace_id", invite["workspace_id"])
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
        )
        if existing_member and existing_member.data:
            raise HTTPException(status_code=409, detail={"error": "User is already a workspace member"})

        accepted = await run_in_threadpool(
            lambda: db.table("workspace_invites")
                .update({"status": "accepted"})
                .eq("id", invite["id"])
                .eq("token", token)
                .eq("status", "pending")
                .execute()
        )
        if not accepted or not accepted.data:
            raise HTTPException(status_code=409, detail={"error": "Invite is no longer pending"})

        try:
            member_res = await run_in_threadpool(
                lambda: db.table("workspace_members")
                    .insert({
                        "workspace_id": invite["workspace_id"],
                        "user_id": user_id,
                        "role": invite["role"],
                    })
                    .execute()
            )
            if not member_res or not member_res.data:
                raise RuntimeError("Workspace membership insert returned no data")
        except (APIError, HTTPError, RuntimeError):
            await run_in_threadpool(
                lambda: db.table("workspace_invites")
                    .update({"status": "pending"})
                    .eq("id", invite["id"])
                    .eq("token", token)
                    .eq("status", "accepted")
                    .execute()
            )
            raise

        metadata = {
            "invite_id": invite["id"],
            "target_user_id": user_id,
            "role": invite["role"],
        }
        await record_workspace_event(
            event_name="team.member_joined",
            workspace_id=invite["workspace_id"],
            actor_user_id=user_id,
            metadata=metadata,
            message=f"A new member joined the workspace as {invite['role'].title()}.",
        )
        await record_workspace_event(
            event_name="permissions.access_granted",
            workspace_id=invite["workspace_id"],
            actor_user_id=user_id,
            metadata=metadata,
            message=f"Workspace access was granted with {invite['role'].title()} role.",
        )
        return {
            "workspace_id": invite["workspace_id"],
            "role": invite["role"],
            "message": "Invite accepted",
        }

    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[accept_invite] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    

async def decline_invite(token: str, user_id: str) -> dict[str, Any]:
    """Invalidate a pending invitation only for its intended authenticated recipient.

    The existing revoked state means the token is unusable. The persisted
    team.invitation_declined event distinguishes recipient decline from
    inviter revocation, without changing database constraints.
    """
    if not _valid_uuid(token):
        raise HTTPException(status_code=400, detail="Invalid token format")
    try:
        result = await run_in_threadpool(lambda: db.table("workspace_invites")
            .select("*").eq("token", token).maybe_single().execute())
        invite = result.data if result else None
        if not invite:
            raise HTTPException(status_code=404, detail="Invite not found")
        auth_result = await run_in_threadpool(lambda: db.auth.admin.get_user_by_id(user_id))
        email = getattr(auth_result.user, "email", None) if auth_result else None
        if not email or email.casefold() != invite["email"].casefold():
            raise HTTPException(status_code=403, detail="Invite email does not match authenticated user")
        if invite["status"] != "pending":
            raise HTTPException(status_code=409, detail="Invite is not pending")
        if datetime.fromisoformat(invite["expires_at"]) <= datetime.now(UTC):
            raise HTTPException(status_code=410, detail="Invite has expired")
        changed = await run_in_threadpool(lambda: db.table("workspace_invites")
            .update({"status": "revoked"}).eq("id", invite["id"])
            .eq("token", token).eq("status", "pending").execute())
        if not changed or not changed.data:
            raise HTTPException(status_code=409, detail="Invite is no longer pending")
        await record_workspace_event(
            event_name="team.invitation_declined", workspace_id=invite["workspace_id"],
            actor_user_id=user_id, metadata={"invite_id": invite["id"], "role": invite["role"]},
            message="The invited recipient declined the workspace invitation.",
        )
        return {"message": "Invitation declined", "workspace_id": invite["workspace_id"]}
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        logger.error("[decline_invite] Error", error=str(exc))
        raise HTTPException(status_code=503, detail="Invitation service unavailable") from exc


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

        if invite["status"] != "pending":
            return {"valid": False, "message": "Invite is not pending"}

        expires_at = datetime.fromisoformat(invite["expires_at"])
        if datetime.now(UTC) > expires_at:
            await run_in_threadpool(
                lambda: db.table("workspace_invites")
                    .update({"status": "expired"})
                    .eq("id", invite["id"])
                    .eq("token", token)
                    .eq("status", "pending")
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

    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
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
    except (APIError, HTTPError, KeyError, TypeError, ValueError) as e:
        logger.error("[get_workspace_invites] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})