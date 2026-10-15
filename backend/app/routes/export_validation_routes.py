"""Export validation API — Kiruthika (compliance). Persistence CRUD owned by Yehor."""

from fastapi import APIRouter, Depends, HTTPException

from app.db.queries.export_queries import (
    get_compliance_validation_payload,
    get_export_job,
)
from app.middlewares.auth import require_auth
from app.schemas.export_contracts import (
    ExportFormat,
    ExportStatus,
    ExportValidationPayload,
    ValidationIssue,
)
from app.services.export_validation_service import (
    run_postflight,
    validation_payload_from_report,
)

router = APIRouter(prefix="/exports", tags=["Export Validation"])


@router.get("/{export_id}/validation", response_model=ExportValidationPayload)
async def get_export_validation(
    export_id: str,
    user: dict = Depends(require_auth),
):
    """
    Compliance validation for an export (Sunny week2 step5 / PR #55).
    Prefer linked compliance_record; otherwise derive from postflight framework.
    """
    user_id = user["user_id"]
    export_row = await get_export_job(export_id, user_id)
    if not export_row:
        raise HTTPException(status_code=404, detail="Export not found")

    fmt = export_row.get("format", "dxf")
    status = export_row.get("status", ExportStatus.VALIDATING.value)

    compliance_id = export_row.get("compliance_record_id")
    if compliance_id:
        record = await get_compliance_validation_payload(compliance_id)
        if record and record.get("validation_payload"):
            payload = record["validation_payload"]
            if isinstance(payload, dict) and "issues" in payload:
                raw_issues = payload.get("issues") or []
                issues = [ValidationIssue(**i) if isinstance(i, dict) else i for i in raw_issues]
                try:
                    fmt_enum = ExportFormat(fmt)
                except ValueError:
                    fmt_enum = ExportFormat.DXF
                try:
                    status_enum = ExportStatus(status)
                except ValueError:
                    status_enum = ExportStatus.VALIDATING
                return ExportValidationPayload(
                    export_id=export_id,
                    status=status_enum,
                    format=fmt_enum,
                    issues=issues,
                )

    report = await run_postflight(export_row)
    data = validation_payload_from_report(export_id, fmt, status, report.issues)
    return ExportValidationPayload(**data)
