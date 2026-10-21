from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RegenerationBrandingTarget(str, Enum):
    CURRENT_PUBLISHED = "current_published"
    ORIGINAL_VERSION = "original_version"


class ReportGenerateRequest(BaseModel):
    project_id: UUID
    template_id: Optional[str] = Field("compliance_summary", description="compliance_summary, revision_report, standard_report, or clash_detection_csv")


class ReportRegenerateRequest(BaseModel):
    branding_target: RegenerationBrandingTarget = RegenerationBrandingTarget.CURRENT_PUBLISHED
    template_id: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: UUID
    status: str
    branding_version_id: Optional[UUID]
    template_version_id: str
    download_url: str
    generated_at: datetime
    provenance_snapshot_id: UUID


class ReportProvenanceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    report_id: UUID
    branding_version_id: Optional[UUID]
    template_version_id: str
    configuration_hash: str
    schema_version: str
    applied_configuration: Dict[str, Any]
    generated_at: datetime