from datetime import datetime

from pydantic import BaseModel, Field

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
    pass


class JobUpdate(BaseModel):
    status: ExportStatus | None = Field(
        None,
        description="Contract-aligned status only — see /api/v1/contracts/export-lifecycle"
    )
    transcript: str | None = None
    error_message: str | None = None


class JobInDB(JobBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class JobResponse(JobInDB):
    pass
