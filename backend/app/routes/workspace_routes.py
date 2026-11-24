from fastapi import APIRouter, Depends, Query

from app.db.queries.workspace_queries import (
    get_my_workspace,
    create_workspace,
    list_accessible_workspaces,
    get_workspace,
    get_workspace_members,
    remove_member,
    update_role_member,
)
from app.middlewares.auth import require_auth
from app.models.workspace_model import (
    MemberRoleUpdate,
    PaginatedMembersResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceCreate,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces_route(user=Depends(require_auth)):
    return await list_accessible_workspaces(user["user_id"])


@router.post("/", response_model=WorkspaceResponse, status_code=201)
async def create_workspace_route(body: WorkspaceCreate, user=Depends(require_auth)):
    return await create_workspace(body.name, user["user_id"])


#GET MY WORKSPACE
@router.get("/me", response_model=WorkspaceResponse)
async def get_my_workspace_route(user=Depends(require_auth)):
    return await get_my_workspace(user["user_id"])

# GET WORKSPACE BY ID
@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_route(
    workspace_id: str,
    user=Depends(require_auth)
):
    return await get_workspace(workspace_id, user["user_id"])

# LIST MEMBERS
@router.get("/{workspace_id}/members", response_model=PaginatedMembersResponse)
async def list_members_route(
    workspace_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user=Depends(require_auth)
):
    return await get_workspace_members(workspace_id, user["user_id"], page, page_size)

# UPDATE MEMBER ROLE
@router.patch("/{workspace_id}/members/{target_user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role_route(
    workspace_id: str,
    target_user_id: str,
    body: MemberRoleUpdate,
    user=Depends(require_auth)
):
    return await update_role_member(workspace_id, target_user_id, body.role, user["user_id"])

# REMOVE MEMBER
@router.delete("/{workspace_id}/members/{target_user_id}")
async def remove_member_route(
    workspace_id: str,
    target_user_id: str,
    user=Depends(require_auth)
):
    removed = await remove_member(workspace_id, target_user_id, user["user_id"])
    if not removed:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"error": "Failed to remove member"})
    return {"message": "Member removed successfully"}