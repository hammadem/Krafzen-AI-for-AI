
from fastapi import APIRouter, Depends, HTTPException

from app.db.queries.invite_queries import (
    accept_invite,
    create_invite,
    decline_invite,
    get_workspace_invites,
    revoke_invite,
    validate_invite,
)
from app.middlewares.auth import require_auth
from app.services.invitation_email_service import send_invitation_email
from app.models.invite_model import (
    InviteAccept,
    InviteCreate,
    InviteResponse,
    InviteValidateResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Invites"])


@router.post("/invites/accept")
async def accept_invite_route(
    body: InviteAccept,
    user=Depends(require_auth)
):
    return await accept_invite(body.token, user["user_id"])


@router.post("/invites/decline")
async def decline_invite_route(body: InviteAccept, user=Depends(require_auth)):
    return await decline_invite(body.token, user["user_id"])


#CREATE INVITE
@router.post("/{workspace_id}/invites",response_model=InviteResponse, status_code=201)
async def create_invite_route(
        workspace_id: str,
        body: InviteCreate,
        user=Depends(require_auth)
):
    invite = await create_invite(workspace_id, body.email, body.role, user["user_id"])
    if not invite:
        raise HTTPException(status_code=503, detail="Invitation could not be created")
    delivery = await send_invitation_email(invite, user["user_id"])
    return {**invite, "email_delivery": delivery}


@router.post("/{workspace_id}/invites/{invite_id}/email")
async def resend_invite_email(workspace_id: str, invite_id: str, user=Depends(require_auth)):
    # Existing owner-scoped query is the authorization boundary. Never trust a
    # recipient, role or token supplied by the browser for a resend.
    invites = await get_workspace_invites(workspace_id, user["user_id"])
    invite = next((row for row in invites if row["id"] == invite_id), None)
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    delivery = await send_invitation_email(invite, user["user_id"])
    return {"id": invite_id, "email_delivery": delivery}

# LIST INVITES
@router.get("/{workspace_id}/invites", response_model=list[InviteResponse])
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
    revoked = await revoke_invite(workspace_id, invite_id, user["user_id"])
    if not revoked:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"error": "Failed to revoke invite"})
    return {"message": "Invite revoked successfully"}

# VALIDATE INVITE (router-level paid authentication currently applies)
@router.get("/invites/validate", response_model=InviteValidateResponse)
async def validate_invite_route(token: str):
    return await validate_invite(token)