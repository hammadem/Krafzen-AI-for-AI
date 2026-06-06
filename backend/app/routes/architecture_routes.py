"""Week 1 architecture contract endpoints for cross-team alignment."""

from fastapi import APIRouter

from app.schemas import (
    ApprovalState,
    CompliancePresetsResponse,
    ExportFormat,
    ExportLifecycleContract,
    ExportValidationPayload,
    ExportStatus,
    JurisdictionContractsResponse,
    JurisdictionSummary,
    CompliancePresetSummary,
)
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


@router.get("/export-model", response_model=ExportModel)
async def get_export_model_template() -> ExportModel:
    """Week 1 canonical ExportModel JSON template for all exporters."""
    return example_export_model()

