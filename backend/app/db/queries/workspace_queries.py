from typing import Any

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.services.activity_service import record_workspace_event
from app.utils.logger import logger
from app.utils.validators import _valid_uuid


#GET WORKSPACE
async def get_workspace(workspace_id:str, user_id: str) -> dict[str, Any] | None:
    if not _valid_uuid(workspace_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid workspace_id"})
    try: 
        res = await run_in_threadpool(
            lambda: db.table("workspaces")
            .select("*")
            .eq("id", workspace_id)
            .maybe_single()
            .execute()
        )
        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "Workspace not found"})
        
         # check user 
        member_res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("user_id")
                .eq("workspace_id", workspace_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
        )

        is_owner = res.data["owner_id"] == user_id
        is_member = bool(member_res and member_res.data)

        if not is_owner and not is_member:
            raise HTTPException(status_code=403, detail={"error": "Access denied"})
        
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_workspace] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    

# GET USER'S WORKSPACE (owner or member)
async def get_my_workspace(user_id: str) -> dict[str, Any] | None:
    try:
        # check if user is an owner first
        res = await run_in_threadpool(
            lambda: db.table("workspaces")
                .select("*")
                .eq("owner_id", user_id)
                .maybe_single()
                .execute()
        )

        if res and res.data:
            return res.data

        # if not owner, check if user is a member
        member_res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("workspace_id")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
        )

        if not member_res or not member_res.data:
            raise HTTPException(status_code=404, detail={"error": "No workspace found"})

        workspace_id = member_res.data["workspace_id"]

        workspace_res = await run_in_threadpool(
            lambda: db.table("workspaces")
                .select("*")
                .eq("id", workspace_id)
                .maybe_single()
                .execute()
        )

        if not workspace_res or not workspace_res.data:
            raise HTTPException(status_code=404, detail={"error": "Workspace not found"})

        return workspace_res.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_my_workspace] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})

#LIST MEMBERS OF A WORKSPACE
async def  get_workspace_members(workspace_id: str,user_id: str,page: int = 1,page_size: int = 20) ->dict[str, Any]:
    if not _valid_uuid(workspace_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid workspace_id"})
    try: 
        await get_workspace(workspace_id, user_id)

        offset = (page -1) * page_size

        res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("*", count="exact")
                .eq("workspace_id", workspace_id)
                .range(offset, offset + page_size - 1)
                .execute()
        )

        members = res.data if res and res.data else []
        total = res.count if res and res.count else 0

        # enrich members with email and display_name from auth
        enriched = []
        for member in members:
            try:
                user_res = await run_in_threadpool(
                    lambda uid=member["user_id"]: db.auth.admin.get_user_by_id(uid)
                )
                member["email"] = user_res.user.email if user_res and user_res.user else None
                member["display_name"] = user_res.user.user_metadata.get("full_name") if user_res and user_res.user else None
            except Exception:
                member["email"] = None
                member["display_name"] = None
            enriched.append(member)

        return {
            "members": enriched,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_workspace_members] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})
    
# UPDATE MEMBER ROLE
async def update_role_member(workspace_id: str, target_user_id: str, new_role: str, user_id: str) -> dict[str, Any] | None:
    if not _valid_uuid(workspace_id) or not _valid_uuid(target_user_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid ID format"})
    
    if new_role not in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail={"error": "Invalid role"})
    
    try:
        workspace = await get_workspace(workspace_id, user_id)

        if workspace["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only owner can update roles"})

        member_res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("*")
                .eq("workspace_id", workspace_id)
                .eq("user_id", target_user_id)
                .maybe_single()
                .execute()
        )
        if not member_res or not member_res.data:
            raise HTTPException(status_code=404, detail={"error": "Member not found"})

        previous_role = member_res.data["role"]
        if previous_role == new_role:
            return member_res.data
        
        res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .update({"role": new_role})
                .eq("workspace_id", workspace_id)
                .eq("user_id", target_user_id)
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "Member not found"})

        metadata = {
            "target_user_id": target_user_id,
            "from_role": previous_role,
            "to_role": new_role,
        }
        await record_workspace_event(
            event_name="team.role_changed",
            workspace_id=workspace_id,
            actor_user_id=user_id,
            metadata=metadata,
            message=f"Workspace member {target_user_id} role changed from {previous_role.title()} to {new_role.title()}.",
        )
        await record_workspace_event(
            event_name="permissions.permission_changed",
            workspace_id=workspace_id,
            actor_user_id=user_id,
            metadata=metadata,
            message=f"Workspace permissions changed for member {target_user_id} from {previous_role.title()} to {new_role.title()}.",
        )
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[update_member_role] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})


#REMOVE MEMBER
async def remove_member(workspace_id: str,target_user_id: str,user_id: str) -> bool: 
    if not _valid_uuid(workspace_id) or not _valid_uuid(target_user_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid ID format"})
    
    try:
        workspace = await get_workspace(workspace_id, user_id)

        if workspace["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only owner can remove members"})

        if target_user_id == user_id:
            raise HTTPException(status_code=400, detail={"error": "Owner cannot remove themselves"})
        
        res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .delete()
                .eq("workspace_id", workspace_id)
                .eq("user_id", target_user_id)
                .execute()
        )

        if not res or not res.data:
            return False

        metadata = {
            "target_user_id": target_user_id,
            "role": res.data[0].get("role"),
        }
        await record_workspace_event(
            event_name="team.member_removed",
            workspace_id=workspace_id,
            actor_user_id=user_id,
            metadata=metadata,
            message=f"Workspace member {target_user_id} was removed.",
        )
        await record_workspace_event(
            event_name="permissions.access_revoked",
            workspace_id=workspace_id,
            actor_user_id=user_id,
            metadata=metadata,
            message=f"Workspace access was revoked for member {target_user_id}.",
        )
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[remove_member] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})