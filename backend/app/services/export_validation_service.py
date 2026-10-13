"""
Export validation preflight/postflight framework — Kiruthika (compliance architecture).

Called by worker_service during VALIDATION_PRECHECK and INTEGRITY_VERIFICATION stages.
Rule execution expands in Week 3+; Week 2 freezes contract shape and gate behavior.
"""

from typing import Any

from app.schemas.export_contracts import (
    ExportFormat,
    PipelineStage,
    PostflightReport,
    PreflightReport,
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)


def _issue(
    code: str,
    message: str,
    *,
    category: ValidationCategory = ValidationCategory.EXPORT_INTEGRITY,
    severity: ValidationSeverity = ValidationSeverity.ERROR,
    element_ref: str | None = None,
    suggested_fix: str | None = None,
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


async def run_preflight(export_context: dict[str, Any]) -> PreflightReport:
    """
    Preflight checks before PROCESSING. Blocks worker when can_proceed=False.
    export_context: export_jobs row or jobs row with project_id, format, metadata.
    """
    export_id = export_context.get("id")
    issues: list[ValidationIssue] = []

    if not export_context.get("project_id"):
        issues.append(_issue("EXPORT_MISSING_PROJECT", "Export requires a project_id."))

    fmt = export_context.get("format")
    if fmt and fmt not in {f.value for f in ExportFormat}:
        issues.append(_issue("EXPORT_INVALID_FORMAT", f"Unsupported format '{fmt}'."))

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


async def run_postflight(export_context: dict[str, Any]) -> PostflightReport:
    """
    Postflight checks after export generation. Sets requires_review when warnings
    exceed threshold; FAILED transitions handled by worker when passed=False.
    """
    export_id = export_context.get("id")
    issues: list[ValidationIssue] = []

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
    issues: list[ValidationIssue],
) -> dict[str, Any]:
    """Build ExportValidationPayload-compatible dict for GET /exports/{id}/validation."""
    return {
        "export_id": export_id,
        "status": status,
        "format": export_format,
        "issues": [i.model_dump() for i in issues],
    }
