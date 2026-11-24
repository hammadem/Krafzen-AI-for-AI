from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProjectType = Literal["residential", "commercial", "industrial", "institutional", "infrastructure", "mixed_use", "other"]
ProjectStage = Literal["draft", "in_progress", "in_review", "completed"]

class ProjectMetadata(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=8000)
    project_type: ProjectType | None = None
    lifecycle_stage: ProjectStage = "draft"

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("Project name must contain text")
        return value.strip()

class ProjectCreate(ProjectMetadata):
    input_text: str = Field(min_length=1, max_length=20000)

class ProjectUpdate(ProjectMetadata):
    """Only editable project metadata, never derived CAD or ownership."""
    model_config = ConfigDict(extra="forbid")
    input_text: str | None = Field(default=None, min_length=1, max_length=20000)

class ProjectOut(ProjectMetadata):
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
    model_config = ConfigDict(from_attributes=True)
