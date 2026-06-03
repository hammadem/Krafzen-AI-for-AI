from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class InviteCreate(BaseModel):
    email: EmailStr
    role: str = "member" #default - member


class InviteResponse(BaseModel):
    id: str
    workspace_id: str
    email: EmailStr
    invited_by: str
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InviteValidateResponse(BaseModel):
    valid: bool
    workspace_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    message: str