from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.export_contracts import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    project_id: str
    format: ExportFormat
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    source_job_id: str | None = None
    compliance_preset_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExportStatusUpdate(BaseModel):
    status: ExportStatus | None = None
    progress_percent: int | None = None
    file_path: str | None = None
    bucket: str | None = None
    error_message: str | None = None
    error_code: str | None = None
    errors: dict[str, Any] | None = None
    artifact_file_id: str | None = None
    compliance_record_id: str | None = None
    metadata: dict[str, Any] | None = None
    retry_count: int | None = None


class ExportResponse(BaseModel):
    id: str
    project_id: str
    requested_by: str
    format: ExportFormat
    status: ExportStatus
    source_job_id: str | None = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    retry_count: int = Field(default=0, ge=0)
    errors: dict[str, Any] | None = None
    artifact_file_id: str | None = None
    compliance_record_id: str | None = None
    compliance_preset_id: str | None = None
    idempotency_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    bucket: str | None = None
    file_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True