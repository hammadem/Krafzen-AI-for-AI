from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class ExportCreate(BaseModel):
    project_id: str
    format: str  # dxf, ifc, dwg, revit_package
    idempotency_key: str  # required, prevents duplicate exports
    source_job_id: Optional[str] = None  # optional originating job
    metadata: Optional[Dict[str, Any]] = None


class ExportStatusUpdate(BaseModel):
    status: Optional[str] = None  # queued, processing, validating, completed, failed, requires_review, cancelled
    progress_percent: Optional[int] = None
    file_path: Optional[str] = None
    bucket: Optional[str] = None
    error_message: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None
    artifact_file_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_count: Optional[int] = None


class ExportResponse(BaseModel):
    id: str
    project_id: str
    requested_by: str
    format: str
    status: str
    source_job_id: Optional[str] = None
    progress_percent: int = 0
    retry_count: int = 0
    errors: Optional[Dict[str, Any]] = None
    artifact_file_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    idempotency_key: str
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    bucket: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True