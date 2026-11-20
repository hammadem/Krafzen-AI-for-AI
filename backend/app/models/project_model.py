from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel): 
    input_text: str

class ProjectUpdate(BaseModel):
    """Browser users may edit text, not forge AI analyses or generated CAD."""
    model_config = ConfigDict(extra="forbid")
    input_text: str | None = Field(default=None, min_length=1, max_length=20000)

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
    archived_at: datetime | None = None
    archived_by: str | None = None
    restored_at: datetime | None = None
    restored_by: str | None = None

    class Config:
        from_attributes = True  # Allows ORM-ish mapping
