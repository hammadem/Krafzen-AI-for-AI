from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FileBase(BaseModel):
    job_id: str = Field(..., description="Foreign key reference to job")
    file_url: str = Field(..., description="Public or signed URL to the file")
<<<<<<< HEAD
    file_type: str = Field(..., description="Type of the file, e.g., 'dxf', 'json', 'pdf'")
=======
    file_type: str = Field(default="dxf", description="Type of the file, e.g., 'dxf', 'json', 'pdf'")
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9


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
<<<<<<< HEAD
        orm_mode = True
=======
        from_attributes = True
>>>>>>> 2b0a26c080d36b93c0a5bb0cdf3a95ff591dfef9


class FileResponse(FileInDB):
    """Response model for API output"""
    pass
