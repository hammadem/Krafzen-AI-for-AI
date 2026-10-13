from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name:str


class WorkspaceResponse(BaseModel):
    id:str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    email: str | None = None
    display_name: str | None = None
    joined_at: datetime | None = None

    class Config:
        from_attributes = True


class MemberRoleUpdate(BaseModel):
    role: str  # admin, member, viewer


class PaginatedMembersResponse(BaseModel):
    members: list[WorkspaceMemberResponse]
    total: int
    page: int
    page_size: int