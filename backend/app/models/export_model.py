from typing import Optional, Any,Dict
from datetime import datetime
from pydantic import BaseModel

class ExportCreate(BaseModel):
    job_id: str
    project_id: str
    format: Optional[str] = "dxf"


class ExportStatusUpdate(BaseModel):
    status: str  # queued, processing, validating, completed, failed, requires_review
    file_path: Optional[str] = None
    bucket: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ExportResponse(BaseModel):
    id: str
    job_id: str
    project_id: str
    requested_by: str
    status: str
    file_path: Optional[str] = None
    bucket: Optional[str] = None
    format: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True