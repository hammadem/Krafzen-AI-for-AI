"""Shared export/compliance contracts for Week 1 architecture alignment."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ExportStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    VALIDATING = "validating"
    REQUIRES_REVIEW = "requires_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(str, Enum):
    GEOMETRY = "geometry"
    DIMENSION = "dimension"
    ZONING = "zoning"
    OCCUPANCY = "occupancy"
    STRUCTURE = "structure"
    EXPORT_INTEGRITY = "export_integrity"


class ExportFormat(str, Enum):
    DXF = "dxf"
    IFC = "ifc"
    DWG = "dwg"
    REVIT_PACKAGE = "revit_package"


class ApprovalState(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class JurisdictionSummary(BaseModel):
    jurisdiction_id: str
    label: str
    schema_version: int = 1
    status: str = Field(default="active", description="Lifecycle status for availability.")
    supported_exports: List[ExportFormat] = Field(
        default_factory=lambda: [ExportFormat.DXF, ExportFormat.IFC, ExportFormat.DWG]
    )


class CompliancePresetSummary(BaseModel):
    preset_id: str
    jurisdiction_id: str
    label: str
    description: str
    default_approval_state: ApprovalState = ApprovalState.PENDING_REVIEW
    rule_version: str


class JurisdictionContractsResponse(BaseModel):
    jurisdictions: List[JurisdictionSummary] = Field(default_factory=list)


class CompliancePresetsResponse(BaseModel):
    presets: List[CompliancePresetSummary] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    category: ValidationCategory
    severity: ValidationSeverity
    code: str = Field(..., description="Stable issue code for frontend grouping and filtering.")
    message: str
    element_ref: Optional[str] = Field(
        default=None,
        description="Optional pointer to room/door/window/object key in export model.",
    )
    suggested_fix: Optional[str] = None
    jurisdiction: Optional[str] = None
    rule_version: Optional[str] = None
    review_state: Optional[ApprovalState] = Field(
        default=None,
        description="Optional review workflow state (pending_review/approved/rejected).",
    )


class ExportValidationPayload(BaseModel):
    export_id: Optional[str] = None
    status: ExportStatus
    format: ExportFormat
    issues: List[ValidationIssue] = Field(default_factory=list)


class ExportLifecycleContract(BaseModel):
    states: List[ExportStatus] = Field(
        default_factory=lambda: [
            ExportStatus.QUEUED,
            ExportStatus.PROCESSING,
            ExportStatus.VALIDATING,
            ExportStatus.REQUIRES_REVIEW,
            ExportStatus.COMPLETED,
            ExportStatus.FAILED,
            ExportStatus.CANCELLED,
        ]
    )
    terminal_states: List[ExportStatus] = Field(
        default_factory=lambda: [
            ExportStatus.COMPLETED,
            ExportStatus.FAILED,
            ExportStatus.CANCELLED,
        ]
    )
    retryable_states: List[ExportStatus] = Field(
        default_factory=lambda: [
            ExportStatus.FAILED,
            ExportStatus.CANCELLED,
        ]
    )

