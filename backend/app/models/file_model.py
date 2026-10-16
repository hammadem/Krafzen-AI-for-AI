from datetime import datetime

from pydantic import BaseModel, Field

# class FileBase(BaseModel): 
#     job_id: str = Field(..., description="Foreign key reference to job")
#     file_url: str = Field(..., description="Public or signed URL to the file")
#     file_type: str = Field(default="dxf", description="Type of the file, e.g., 'dxf', 'json', 'pdf'")


class FileCreate(BaseModel):
    """Schema for file creation"""
    job_id: str
    project_id: str | None = None
    file_type: str = "dxf"
    path: str
    bucket: str | None = "dxf-files"
    mime_type: str | None = None
    size_bytes: int | None = None
    name: str | None = None


class FileUpdate(BaseModel):
    """Schema for updating existing file entries"""
    #file_url: Optional[str] = Field(None, description="Updated file URL")
    file_type: str | None = Field(None, description="Updated file type")
    path: str | None = None
    name: str | None = None

# class FileInDB(FileBase):
#     """Internal DB model"""
#     id: str
#     created_at: Optional[datetime] = None

#     class Config:
#         from_attributes = True


class FileResponse(BaseModel):
    id: str
    job_id: str
    project_id: str | None = None
    bucket: str
    path: str
    file_type: str
    name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = None

    class Config: 
        from_attributes = True
