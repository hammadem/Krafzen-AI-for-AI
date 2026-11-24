from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Workspace name cannot be blank")
        return value


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