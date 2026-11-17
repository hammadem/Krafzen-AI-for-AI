from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    name: str | None = None
    version: int = Field(default=1, gt=0)
    bucket: str | None = "dxf-files"
    mime_type: str | None = None
    size_bytes: int | None = None


class FileUpdate(BaseModel):
    """Only display names are editable by customers. Storage metadata is immutable."""
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)

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
    version: int = 1
    archived_at: datetime | None = None
    approval_state: str = "pending_review"
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    import_metadata: dict | None = None
    created_at: datetime | None = None

    class Config: 
        from_attributes = True
