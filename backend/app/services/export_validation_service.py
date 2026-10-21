"""
Export validation preflight/postflight framework — Kiruthika (compliance architecture).

Called by worker_service during VALIDATION_PRECHECK and INTEGRITY_VERIFICATION stages.
Rule execution expands in Week 3+; Week 2 freezes contract shape and gate behavior.

Extended for Enterprise Regional Background Processing & Worker Affinity.
"""

import os
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi.concurrency import run_in_threadpool
from app.services.region_registry import CENTRAL_REGION_REGISTRY

from app.schemas.export_contracts import (
    ExportFormat,
    PipelineStage,
    PostflightReport,
    PreflightReport,
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)
from app.services.supabase_service import supabase_service
from app.db.supabase_client import db


def _issue(
    code: str,
    message: str,
    *,
    category: ValidationCategory = ValidationCategory.EXPORT_INTEGRITY,
    severity: ValidationSeverity = ValidationSeverity.ERROR,
    element_ref: Optional[str] = None,
    suggested_fix: Optional[str] = None,
) -> ValidationIssue:
    return ValidationIssue(
        category=category,
        severity=severity,
        code=code,
        message=message,
        element_ref=element_ref,
        suggested_fix=suggested_fix,
        jurisdiction="US_IRC_BASELINE",
        rule_version="us_irc_baseline@1",
    )


async def _check_regional_worker_affinity(
    export_context: Dict[str, Any]
) -> Optional[ValidationIssue]:
    """
    Enforces that worker node region matches tenant's sovereign residency region.
    Supports 'auto'/'dynamic' for local dev and strict pinning for production.
    """
    worker_region = os.getenv("WORKER_REGION_CODE", "auto").strip().lower()
    central_client = supabase_service.client or db

    # Resolve organization_id
    org_id_raw = export_context.get("organization_id")
    project_id = export_context.get("project_id")

    if not org_id_raw and project_id:
        proj_res = await run_in_threadpool(
            lambda: central_client.table("projects")
            .select("workspace_id")
            .eq("id", project_id)
            .maybe_single()
            .execute()
        )
        if proj_res and proj_res.data:
            org_id_raw = proj_res.data.get("workspace_id")

    # If legacy/individual user project, default to global processing
    if not org_id_raw:
        return None

    try:
        org_id = str(UUID(str(org_id_raw)))
    except (ValueError, TypeError):
        return None

    # Query organization_residency to resolve required_region
    residency_res = await run_in_threadpool(
        lambda: central_client.table("organization_residency")
        .select("region_code, status")
        .eq("organization_id", org_id)
        .maybe_single()
        .execute()
    )
    res_data = residency_res.data if residency_res else None

    # Default to "global" if no specific residency entry exists or if status is not active
    required_region = "global"
    if res_data and res_data.get("status") == "active":
        required_region = (res_data.get("region_code") or "global").strip().lower()

    # Dynamic / Local Development Worker Mode ('auto', 'dynamic', or '*')
    if worker_region in ("auto", "dynamic", "*"):
        # Validate that the requested region is actually supported in the registry
        if required_region != "global" and required_region not in CENTRAL_REGION_REGISTRY:
            return _issue(
                code="UNSUPPORTED_REGION",
                message=f"Requested sovereign region '{required_region}' is not registered in the system.",
                category=ValidationCategory.EXPORT_INTEGRITY,
                severity=ValidationSeverity.CRITICAL,
                suggested_fix="Register the region in CENTRAL_REGION_REGISTRY before dispatching jobs.",
            )
        return None

    # Strict Production Worker Mode (Pinned Node Verification)
    if worker_region != required_region:
        return _issue(
            code="REGIONAL_WORKER_MISMATCH",
            message=(
                f"Job requires processing on a worker in sovereign region '{required_region}', "
                f"but this worker is pinned to region '{worker_region}'."
            ),
            category=ValidationCategory.EXPORT_INTEGRITY,
            severity=ValidationSeverity.CRITICAL,
            suggested_fix=(
                f"Route this export job to a worker pool configured with WORKER_REGION_CODE={required_region}."
            ),
        )

    return None


async def run_preflight(export_context: Dict[str, Any]) -> PreflightReport:
    """
    Preflight checks before PROCESSING. Blocks worker when can_proceed=False.
    export_context: export_jobs row or jobs row with project_id, format, metadata.
    """
    export_id = export_context.get("id")
    issues: List[ValidationIssue] = []

    # Regional worker affinity gate (Zero Silent Fallback)
    affinity_issue = await _check_regional_worker_affinity(export_context)
    if affinity_issue:
        issues.append(affinity_issue)

    # Project ID validation
    if not export_context.get("project_id"):
        issues.append(_issue("EXPORT_MISSING_PROJECT", "Export requires a project_id."))

    # Format validation
    fmt = export_context.get("format")
    if fmt and fmt not in {f.value for f in ExportFormat}:
        issues.append(_issue("EXPORT_INVALID_FORMAT", f"Unsupported format '{fmt}'."))

    # 4. Idempotency validation
    metadata = export_context.get("metadata") or {}
    if not metadata.get("idempotency_key") and not export_context.get("idempotency_key"):
        issues.append(
            _issue(
                "EXPORT_MISSING_IDEMPOTENCY",
                "idempotency_key is required for export requests.",
                severity=ValidationSeverity.WARNING,
            )
        )

    blocking = [i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]
    return PreflightReport(
        export_id=export_id,
        can_proceed=len(blocking) == 0,
        issues=issues,
        checked_at_stage=PipelineStage.VALIDATION_PRECHECK,
    )


async def run_postflight(export_context: Dict[str, Any]) -> PostflightReport:
    """
    Postflight checks after export generation. Sets requires_review when warnings
    exceed threshold; FAILED transitions handled by worker when passed=False.
    """
    export_id = export_context.get("id")
    issues: List[ValidationIssue] = []

    if not export_context.get("artifact_file_id"):
        issues.append(
            _issue(
                "EXPORT_MISSING_ARTIFACT",
                "No artifact_file_id linked after export generation.",
                category=ValidationCategory.EXPORT_INTEGRITY,
                severity=ValidationSeverity.WARNING,
            )
        )

    metadata = export_context.get("metadata") or {}
    stage = metadata.get("stage")
    if stage and stage != PipelineStage.ARTIFACT_STORAGE.value:
        issues.append(
            _issue(
                "EXPORT_INCOMPLETE_PIPELINE",
                f"Pipeline stopped at stage '{stage}' before artifact_storage.",
                severity=ValidationSeverity.WARNING,
            )
        )

    blocking = [i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]
    metadata = export_context.get("metadata") or {}
    requires_review = metadata.get("requires_review") is True

    return PostflightReport(
        export_id=export_id,
        passed=len(blocking) == 0,
        requires_review=requires_review,
        issues=issues,
        checked_at_stage=PipelineStage.INTEGRITY_VERIFICATION,
    )


def validation_payload_from_report(
    export_id: str,
    export_format: str,
    status: str,
    issues: List[ValidationIssue],
) -> Dict[str, Any]:
    """Build ExportValidationPayload-compatible dict for GET /exports/{id}/validation."""
    return {
        "export_id": export_id,
        "status": status,
        "format": export_format,
        "issues": [i.model_dump() for i in issues],
    }
