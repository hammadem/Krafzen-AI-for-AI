from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FileBase(BaseModel):
    job_id: str = Field(..., description="Foreign key reference to job")
    file_url: str = Field(..., description="Public or signed URL to the file")
    file_type: str = Field(default="dxf", description="Type of the file, e.g., 'dxf', 'json', 'pdf'")


class FileCreate(FileBase):
    """Schema for file creation"""
    pass


class FileUpdate(BaseModel):
    """Schema for updating existing file entries"""
    file_url: Optional[str] = Field(None, description="Updated file URL")
    file_type: Optional[str] = Field(None, description="Updated file type")


class FileInDB(FileBase):
    """Internal DB model"""
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileResponse(FileInDB):
    """Response model for API output"""
    pass
