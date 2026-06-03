from fastapi import APIRouter, Depends
from app.middlewares.auth import require_auth
from app.models.invite_model import (
    InviteCreate,
    InviteResponse,
    InviteValidateResponse
)
from app.db.queries.invite_queries import (
    create_invite,
    revoke_invite,
    validate_invite,
    get_workspace_invites
)
from typing import List

router = APIRouter(prefix="/workspaces", tags=["Invites"])

#CREATE INVITE
@router.post("/{workspace_id}/invites",response_model=InviteResponse, status_code=201)
async def create_invite_route(
        workspace_id: str,
        body: InviteCreate,
        user=Depends(require_auth)
):
    return await create_invite(workspace_id, body.email, body.role, user["user_id"])

# LIST INVITES
@router.get("/{workspace_id}/invites", response_model=List[InviteResponse])
async def list_invites_route(
    workspace_id: str,
    user=Depends(require_auth)
):
    return await get_workspace_invites(workspace_id, user["user_id"])


# REVOKE INVITE
@router.patch("/{workspace_id}/invites/{invite_id}/revoke")
async def revoke_invite_route(
    workspace_id: str,
    invite_id: str,
    user=Depends(require_auth)
):
    revoked = await revoke_invite(invite_id, user["user_id"])
    if not revoked:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"error": "Failed to revoke invite"})
    return {"message": "Invite revoked successfully"}

# VALIDATE INVITE (public - no auth required)
@router.get("/invites/validate", response_model=InviteValidateResponse)
async def validate_invite_route(token: str):
    return await validate_invite(token)