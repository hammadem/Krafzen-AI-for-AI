from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.export_contracts import ExportStatus


class JobBase(BaseModel):
    project_id: str = Field(..., description="Foreign key reference to project")
    status: ExportStatus = Field(
        default=ExportStatus.QUEUED,
        description="Job lifecycle status — must align with /api/v1/contracts/export-lifecycle"
    )
    transcript: str | None = Field(None, description="Job transcript text or notes")
    error_message: str | None = Field(None, description="Error details if job failed")


class JobCreate(JobBase):
    """The client can enqueue a job, not forge a completed/failed job."""
    status: Literal[ExportStatus.QUEUED] = ExportStatus.QUEUED


class JobUpdate(BaseModel):
    """Customers may correct transcript text, but not lifecycle or worker errors."""
    model_config = ConfigDict(extra="forbid")
    transcript: str | None = None


class JobInDB(JobBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class JobResponse(JobInDB):
    pass
