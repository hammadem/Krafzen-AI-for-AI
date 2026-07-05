from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.export_contracts import ExportStatus


class JobBase(BaseModel):
    project_id: str = Field(..., description="Foreign key reference to project")
    status: ExportStatus = Field(
        default=ExportStatus.QUEUED,
        description="Job lifecycle status — must align with /api/v1/contracts/export-lifecycle"
    )
    transcript: Optional[str] = Field(None, description="Job transcript text or notes")
    error_message: Optional[str] = Field(None, description="Error details if job failed")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[ExportStatus] = Field(
        None,
        description="Contract-aligned status only — see /api/v1/contracts/export-lifecycle"
    )
    transcript: Optional[str] = None
    error_message: Optional[str] = None


class JobInDB(JobBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobResponse(JobInDB):
    pass
