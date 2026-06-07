from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.export_contracts import ExportStatus, ExportFormat


class ExportCreate(BaseModel):
    project_id: str
    format: ExportFormat
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    source_job_id: Optional[str] = None
    compliance_preset_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportStatusUpdate(BaseModel):
    status: Optional[ExportStatus] = None
    progress_percent: Optional[int] = None
    file_path: Optional[str] = None
    bucket: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None
    artifact_file_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_count: Optional[int] = None


class ExportResponse(BaseModel):
    id: str
    project_id: str
    requested_by: str
    format: ExportFormat
    status: ExportStatus
    source_job_id: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    retry_count: int = Field(default=0, ge=0)
    errors: Optional[Dict[str, Any]] = None
    artifact_file_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    compliance_preset_id: Optional[str] = None
    idempotency_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    bucket: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True