from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.core.permissions import EnterprisePermission
from app.middlewares.auth import require_auth
from app.middlewares.permissions import require_permission
from app.schemas.report_generation import (
    ReportGenerateRequest,
    ReportProvenanceResponse,
    ReportRegenerateRequest,
    ReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/enterprise/reports", tags=["Enterprise White-Label Reports"])


def get_report_service() -> ReportService:
    return ReportService()

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: ReportGenerateRequest,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.REPORT_GENERATE)),
    service: ReportService = Depends(get_report_service),
):
    """
    Generates a branded report using the active published branding version.
    Rejects unbrandable export formats (like CSV) with 422 FORMAT_DOES_NOT_SUPPORT_BRANDING..
    """
    return service.generate_report(
        organization_id=organization_id,
        project_id=payload.project_id,
        template_id=payload.template_id,
    )


@router.post("/{report_id}/regenerate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def regenerate_report(
    report_id: UUID,
    payload: ReportRegenerateRequest,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.REPORT_GENERATE)),
    service: ReportService = Depends(get_report_service),
):
    """
    Non-destructively regenerates a report against published branding
    or the original snapshot version. Mints a unique report_id.
    Requires: Enterprise report generate.
    """
    return service.regenerate_report(
        organization_id=organization_id,
        source_report_id=report_id,
        branding_target=payload.branding_target,
        template_id=payload.template_id,
    )


@router.get("/{report_id}/provenance", response_model=ReportProvenanceResponse, status_code=status.HTTP_200_OK)
async def get_report_provenance(
    report_id: UUID,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.REPORT_ACCESS)),
    service: ReportService = Depends(get_report_service),
):
    """
    Retrieves the immutable audit record from report_branding_snapshots for a generated artifact.
    Requires: Authorized report access.
    """
    return service.get_report_provenance(
        organization_id=organization_id,
        report_id=report_id,
    )