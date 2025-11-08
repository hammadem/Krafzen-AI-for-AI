from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobBase(BaseModel):
    project_id: str = Field(..., description="Foreign key reference to project")
    status: Optional[str] = Field(default="pending", description="Job status, e.g., pending, running, completed, failed")
    transcript: Optional[str] = Field(None, description="Job transcript text or notes")
    error_message: Optional[str] = Field(None, description="Error details if job failed")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Updated job status")
    transcript: Optional[str] = Field(None, description="Updated transcript content")
    error_message: Optional[str] = Field(None, description="Updated error message")


class JobInDB(JobBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class JobResponse(JobInDB):
    pass
