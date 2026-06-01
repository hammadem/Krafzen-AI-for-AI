from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class WorkspaceCreate(BaseModel):
    name:str


class WorkspaceResponse(BaseModel):
    id:str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemberRoleUpdate(BaseModel):
    role: str  # admin, member, viewer


class PaginatedMembersResponse(BaseModel):
    members: List[WorkspaceMemberResponse]
    total: int
    page: int
    page_size: int