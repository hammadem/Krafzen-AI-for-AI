from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProjectCreate(BaseModel): 
    input_text: str

class ProjectUpdate(BaseModel):
    input_text: str | None = None
    parsed_json: dict[str, Any] | None = None
    image_url: str | None = None
    dxf_url: str | None = None
    dwg_url: str | None = None

class ProjectOut(BaseModel):
    id: str
    user_id: str
    input_text: str
    parsed_json: dict[str, Any] | None = None
    image_url: str | None = None
    dxf_url: str | None = None
    dwg_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True  # Allows ORM-ish mapping
