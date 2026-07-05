"""Week 1–2 architecture contract endpoints for cross-team alignment."""

from fastapi import APIRouter

from app.core.export_stage_catalog import REVIT_ELEMENT_MAPPINGS
from app.schemas import (
    ApprovalState,
    CompliancePresetsResponse,
    ExportFormat,
    ExportLifecycleContract,
    ExportProgressContract,
    ExportProgressFieldSpec,
    ExportStageCatalog,
    ExportValidationPayload,
    ExportStatus,
    JurisdictionContractsResponse,
    JurisdictionSummary,
    CompliancePresetSummary,
    RevitCompatibilitySpec,
    RevitElementMapping,
)
from app.services.export_pipeline_service import get_stage_catalog
from app.schemas.export_model import ExportModel, example_export_model

router = APIRouter(prefix="/contracts", tags=["Architecture Contracts"])


@router.get("/export-lifecycle", response_model=ExportLifecycleContract)
async def get_export_lifecycle_contract() -> ExportLifecycleContract:
    """Single source of truth for export lifecycle states."""
    return ExportLifecycleContract()


@router.get("/validation-template", response_model=ExportValidationPayload)
async def get_validation_template() -> ExportValidationPayload:
    """Template payload for frontend/worker/backend contract alignment."""
    return ExportValidationPayload(
        export_id="example-export-id",
        status=ExportStatus.VALIDATING,
        format=ExportFormat.DXF,
        issues=[],
    )


@router.get("/jurisdictions", response_model=JurisdictionContractsResponse)
async def get_jurisdiction_contracts() -> JurisdictionContractsResponse:
    """Week 1 jurisdiction catalog contract for backend/frontend alignment."""
    return JurisdictionContractsResponse(
        jurisdictions=[
            JurisdictionSummary(
                jurisdiction_id="US_IRC_BASELINE",
                label="USA (IRC baseline screening)",
                schema_version=1,
                supported_exports=[ExportFormat.DXF, ExportFormat.IFC, ExportFormat.DWG],
            )
        ]
    )


@router.get("/compliance-presets", response_model=CompliancePresetsResponse)
async def get_compliance_presets() -> CompliancePresetsResponse:
    """Week 1 compliance preset contract for UI and workflow wiring."""
    return CompliancePresetsResponse(
        presets=[
            CompliancePresetSummary(
                preset_id="us-irc-baseline-v1",
                jurisdiction_id="US_IRC_BASELINE",
                label="US IRC Baseline (MVP)",
                description=(
                    "Screening-oriented baseline checks for room size, door width, "
                    "stairs, and egress thresholds. Not legal approval."
                ),
                default_approval_state=ApprovalState.PENDING_REVIEW,
                rule_version="us_irc_baseline@1",
            )
        ]
    )


@router.get("/workflow-spec")
async def get_workflow_spec() -> dict:
    """Week 1 implementation workflow spec for backend/worker/frontend coordination."""
    return {
        "pipeline_stages": [
            "validation_precheck",
            "preprocessing",
            "geometry_transformation",
            "metadata_injection",
            "export_generation",
            "integrity_verification",
            "artifact_storage",
        ],
        "status_machine": [
            "queued",
            "processing",
            "validating",
            "requires_review",
            "completed",
            "failed",
            "cancelled",
        ],
        "retry_policy": {
            "retryable_states": ["failed", "cancelled"],
            "max_retries_default": 3,
            "requires_idempotency_key": True,
        },
        "coordination_contracts": {
            "backend_owner": "Yehor",
            "queue_owner": "Tazwar",
            "compliance_owner": "Kiruthika",
            "frontend_owner": "Sunny",
        },
        "supported_formats": ["dxf", "ifc", "dwg", "revit_package"],
    }


@router.get("/export-stages", response_model=ExportStageCatalog)
async def get_export_stage_gates() -> ExportStageCatalog:
    """Week 2: pipeline stage entry/exit rules for Tazwar worker — do not skip gates."""
    return get_stage_catalog()


@router.get("/export-progress-contract", response_model=ExportProgressContract)
async def get_export_progress_contract() -> ExportProgressContract:
    """Week 2: frozen frontend export history/progress shape (Sunny PR #55 alignment)."""
    lifecycle = ExportLifecycleContract()
    status_labels = {
        ExportStatus.QUEUED.value: "Queued",
        ExportStatus.PROCESSING.value: "Processing",
        ExportStatus.VALIDATING.value: "Validating",
        ExportStatus.REQUIRES_REVIEW.value: "Requires review",
        ExportStatus.COMPLETED.value: "Completed",
        ExportStatus.FAILED.value: "Failed",
        ExportStatus.CANCELLED.value: "Cancelled",
    }
    return ExportProgressContract(
        response_fields=[
            ExportProgressFieldSpec(
                name="id", type="uuid", required=True, description="export_jobs primary key"
            ),
            ExportProgressFieldSpec(
                name="project_id", type="uuid", required=True, description="Parent project"
            ),
            ExportProgressFieldSpec(
                name="format", type="enum", required=True, description="dxf|ifc|dwg|revit_package"
            ),
            ExportProgressFieldSpec(
                name="status", type="enum", required=True, description="Lifecycle status"
            ),
            ExportProgressFieldSpec(
                name="progress_percent",
                type="integer",
                required=True,
                description="0–100 while processing/validating",
            ),
            ExportProgressFieldSpec(
                name="retry_count", type="integer", required=True, description="Retry attempts"
            ),
            ExportProgressFieldSpec(
                name="artifact_file_id",
                type="uuid",
                required=False,
                description="Link to files row; use signed URL for download",
            ),
            ExportProgressFieldSpec(
                name="error_message", type="string", required=False, description="Failure detail"
            ),
            ExportProgressFieldSpec(
                name="file_path",
                type="string",
                required=False,
                description="Denormalized files.path for display",
            ),
            ExportProgressFieldSpec(
                name="created_at", type="datetime", required=True, description="Row created"
            ),
        ],
        status_labels=status_labels,
        in_progress_states=[ExportStatus.PROCESSING, ExportStatus.VALIDATING],
        retryable_states=lifecycle.retryable_states,
        terminal_states=lifecycle.terminal_states,
    )


@router.get("/revit-compatibility-mapping", response_model=RevitCompatibilitySpec)
async def get_revit_compatibility_mapping() -> RevitCompatibilitySpec:
    """Week 2: Revit package metadata mapping — Phase 1 (no native .rvt generation)."""
    return RevitCompatibilitySpec(
        element_mappings=[RevitElementMapping(**m) for m in REVIT_ELEMENT_MAPPINGS],
        example_manifest={
            "package_version": "1.0",
            "source_export_id": "example-export-id",
            "project_id": "example-project-id",
            "levels": ["Level 1"],
            "geometry_ref": "files/{artifact_file_id}",
            "compliance_record_id": "optional-uuid",
            "element_mappings": REVIT_ELEMENT_MAPPINGS,
        },
    )


@router.get("/preflight-template")
async def get_preflight_template() -> dict:
    """Week 2: preflight report shape for worker integration."""
    return {
        "can_proceed": True,
        "checked_at_stage": "validation_precheck",
        "issues": [],
    }


@router.get("/postflight-template")
async def get_postflight_template() -> dict:
    """Week 2: postflight report shape for worker integration."""
    return {
        "passed": True,
        "requires_review": False,
        "checked_at_stage": "integrity_verification",
        "issues": [],
    }


@router.get("/export-model", response_model=ExportModel)
async def get_export_model_template() -> ExportModel:
    """Week 1 canonical ExportModel JSON template for all exporters."""
    return example_export_model()

