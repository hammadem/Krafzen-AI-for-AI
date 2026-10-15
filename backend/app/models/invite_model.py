from datetime import datetime

from pydantic import BaseModel, EmailStr


class InviteCreate(BaseModel):
    email: EmailStr
    role: str = "member" #default - member


class InviteAccept(BaseModel):
    token: str


class InviteResponse(BaseModel):
    id: str
    workspace_id: str
    email: EmailStr
    invited_by: str
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class InviteValidateResponse(BaseModel):
    valid: bool
    workspace_id: str | None = None
    email: str | None = None
    role: str | None = None
    message: str