from typing import Optional, List, Dict, Any
import uuid
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.utils.logger import logger



# Helper
def _valid_uuid(value: str)-> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False
    

#GET WORKSPACE
async def get_workspace(workspace_id:str, user_id: str) -> Optional[Dict[str, Any]]:
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
    

# GET USER'S WORKSPACE
async def get_my_workspace(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = await run_in_threadpool(
            lambda: db.table("workspaces")
                .select("*")
                .eq("owner_id", user_id)
                .maybe_single()
                .execute()
        )
        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "No workspace found"})
        return res.data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[get_my_workspace] Error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Server error"})

#LIST MEMBERS OF A WORKSPACE
async def  get_workspace_members(workspace_id: str,user_id: str,page: int = 1,page_size: int = 20) ->Dict[str, Any]:
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

        return {
            "members": members,
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
async def update_role_member(workspace_id: str, target_user_id: str, new_role: str, user_id: str) -> Optional[Dict[str, Any]]:
    if not _valid_uuid(workspace_id) or not _valid_uuid(target_user_id):
        raise HTTPException(status_code=400, detail={"error": "Invalid ID format"})
    
    if new_role not in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail={"error": "Invalid role"})
    
    try:
        workspace = await get_workspace(workspace_id, user_id)

        if workspace["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail={"error": "Only owner can update roles"})
        
        res = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .update({"role": new_role})
                .eq("workspace_id", workspace_id)
                .eq("user_id", target_user_id)
                .execute()
        )

        if not res or not res.data:
            raise HTTPException(status_code=404, detail={"error": "Member not found"})

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

        return bool(res and res.data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[remove_member] Error", error=str(e), exc_info=True)
        return False