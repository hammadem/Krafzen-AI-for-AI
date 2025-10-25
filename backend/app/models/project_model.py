"""Pydantic models for validation."""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ProjectBase(BaseModel):
    user_id: str
    input_text: str

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    parsed_json: Optional[Dict] = None
    dxf_url: Optional[str] = None

    class Config:
        from_attributes = True
