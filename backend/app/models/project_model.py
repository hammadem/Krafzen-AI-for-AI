from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ProjectCreate(BaseModel):
    input_text: str

class ProjectUpdate(BaseModel):
    input_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    dxf_url: Optional[str] = None
    dwg_url: Optional[str] = None

class ProjectOut(BaseModel):
    id: str
    user_id: str
    input_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    dxf_url: Optional[str] = None
    dwg_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows ORM-ish mapping
