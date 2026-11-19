"""Export generation gate.

Do not create files that only *look* like DXF, DWG, or IFC. The export worker
already marks raised exceptions as FAILED; this gate prevents false-success
artifacts until real, project-backed generators are integrated and validated.
"""

from typing import Any

from app.core.export_stage_catalog import EXPORT_STAGE_CATALOG
from app.schemas.export_contracts import ExportFormat, PipelineStage
from app.services.export_validation_service import run_postflight, run_preflight
from app.utils.logger import logger


class ExportGenerationUnavailableError(RuntimeError):
    """No verified, project-backed generator is connected to this export pipeline."""


async def run_export_generation(job: dict[str, Any]) -> dict[str, Any]:
    """Fail closed instead of saving sample bytes under an engineering extension.

    The worker catches this exception, sets export_jobs status to FAILED and
    emits a failure event/notification. Never return an artifact_file_id when
    no real generator has produced a validated file.
    """
    project_id = job.get("project_id")
    export_format = str(job.get("format") or "").strip().lower()

    if not project_id:
        raise ValueError("Export generation requires a project_id")
    if export_format not in {fmt.value for fmt in ExportFormat}:
        raise ValueError(f"Unsupported export format: {export_format or '(missing)'}")

    logger.error(
        "[export_pipeline] refusing placeholder export",
        job_id=job.get("id"),
        project_id=str(project_id),
        format=export_format,
        stage=PipelineStage.EXPORT_GENERATION.value,
    )
    raise ExportGenerationUnavailableError(
        f"{export_format.upper()} export is not available: a verified generator "
        "using actual project data is not connected to this pipeline."
    )


async def run_preflight_gate(export_context: dict[str, Any]):
    """Run preflight; worker must fail the job if can_proceed is False."""
    report = await run_preflight(export_context)
    if not report.can_proceed:
        logger.warning(
            "[export_pipeline] preflight blocked",
            export_id=export_context.get("id"),
            issue_count=len(report.issues),
        )
    return report


async def run_postflight_gate(export_context: dict[str, Any]):
    """Run postflight; worker uses passed/requires_review for status routing."""
    return await run_postflight(export_context)


def get_stage_catalog():
    return EXPORT_STAGE_CATALOG
