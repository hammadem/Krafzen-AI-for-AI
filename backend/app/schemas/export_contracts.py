"""Shared export/compliance contracts for Week 1–2 architecture alignment."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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


# ── Week 2: persistence + frontend progress contract (Yehor / Sunny) ──────────


class ExportCreate(BaseModel):
    """Request body for POST /api/v1/exports (Yehor persistence layer)."""

    project_id: str
    format: ExportFormat
    source_job_id: Optional[str] = None
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    compliance_preset_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportResponse(BaseModel):
    """
    Canonical export row for list/detail APIs and Sunny PR #55 export history UI.
    `file_path` is denormalized from linked files.path for display/download wiring.
    """

    id: str
    project_id: str
    format: ExportFormat
    status: ExportStatus
    progress_percent: int = Field(default=0, ge=0, le=100)
    retry_count: int = Field(default=0, ge=0)
    artifact_file_id: Optional[str] = None
    compliance_record_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportListResponse(BaseModel):
    exports: List[ExportResponse] = Field(default_factory=list)
    total: int = 0


class ExportProgressFieldSpec(BaseModel):
    """Documents one field in ExportResponse for frontend contract sync."""

    name: str
    type: str
    required: bool
    description: str


class ExportProgressContract(BaseModel):
    """
    Frontend export progress/error contract (Sunny week2 step4+).
    Mirrors export_contracts enums — no page-specific payload variants.
    """

    response_fields: List[ExportProgressFieldSpec]
    status_labels: Dict[str, str]
    in_progress_states: List[ExportStatus]
    retryable_states: List[ExportStatus]
    terminal_states: List[ExportStatus]
    download_via: str = Field(
        default="artifact_file_id",
        description="Use files signed-url endpoint with this id when status=completed.",
    )
    retry_endpoint: str = Field(default="POST /api/v1/exports/{export_id}/retry")
    validation_endpoint: str = Field(default="GET /api/v1/exports/{export_id}/validation")


# ── Week 2: pipeline stage gates (Tazwar worker) ────────────────────────────


class PipelineStage(str, Enum):
    VALIDATION_PRECHECK = "validation_precheck"
    PREPROCESSING = "preprocessing"
    GEOMETRY_TRANSFORMATION = "geometry_transformation"
    METADATA_INJECTION = "metadata_injection"
    EXPORT_GENERATION = "export_generation"
    INTEGRITY_VERIFICATION = "integrity_verification"
    ARTIFACT_STORAGE = "artifact_storage"


class StageGateRule(BaseModel):
    stage: PipelineStage
    entry_status: ExportStatus
    exit_status: ExportStatus
    on_failure_status: ExportStatus = ExportStatus.FAILED
    requires_preflight: bool = False
    requires_postflight: bool = False
    description: str


class ExportStageCatalog(BaseModel):
    """Entry/exit rules for export pipeline stages — worker must not skip gates."""

    stages: List[StageGateRule]
    max_retries_default: int = 3
    requires_idempotency_key: bool = True


# ── Week 2: validation preflight / postflight framework ─────────────────────


class PreflightReport(BaseModel):
    export_id: Optional[str] = None
    can_proceed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    checked_at_stage: PipelineStage = PipelineStage.VALIDATION_PRECHECK


class PostflightReport(BaseModel):
    export_id: Optional[str] = None
    passed: bool
    requires_review: bool = False
    issues: List[ValidationIssue] = Field(default_factory=list)
    checked_at_stage: PipelineStage = PipelineStage.INTEGRITY_VERIFICATION


# ── Week 2: Revit-compatible package mapping (Phase 1 — no native .rvt) ─────


class RevitElementMapping(BaseModel):
    krafzen_type: str
    revit_category: str
    revit_family_hint: Optional[str] = None
    parameter_map: Dict[str, str] = Field(default_factory=dict)


class RevitPackageManifest(BaseModel):
    """
    Metadata bundle for revit_package format.
    Plugin Phase 2 consumes this JSON; MVP stores it alongside DXF/IFC/DWG artifacts.
    """

    package_version: str = "1.0"
    source_export_id: str
    project_id: str
    levels: List[str] = Field(default_factory=list)
    element_mappings: List[RevitElementMapping] = Field(default_factory=list)
    geometry_ref: Optional[str] = Field(
        default=None,
        description="Pointer to canonical ExportModel JSON or artifact file id.",
    )
    compliance_record_id: Optional[str] = None


class RevitCompatibilitySpec(BaseModel):
    phase: str = Field(default="1", description="1 = metadata package only; 2 = native add-in")
    native_rvt_generation: bool = False
    supported_revit_versions: List[str] = Field(
        default_factory=lambda: ["2022", "2023", "2024", "2025"]
    )
    package_format: str = "revit_package"
    element_mappings: List[RevitElementMapping] = Field(default_factory=list)
    example_manifest: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sample revit_package JSON bundle shape for Yehor/Tazwar artifact metadata.",
    )

