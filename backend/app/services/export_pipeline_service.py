"""
Export pipeline orchestration hooks — Kiruthika (Week 2).

Bridges Tazwar's worker to existing DXF/IFC/DWG paths. Generation is stubbed until
Yehor export_jobs + artifact handoff land; stage metadata is written for postflight.
"""

import asyncio
from typing import Any

from app.core.export_stage_catalog import EXPORT_STAGE_CATALOG
from app.schemas.export_contracts import PipelineStage
from app.services.export_validation_service import run_postflight, run_preflight
from app.utils.logger import logger


async def run_export_generation(job: dict[str, Any]) -> dict[str, Any]:
    """
    PROCESSING stage: existing format exporters plug in here (Week 2+).
    Returns metadata patch to merge onto export_jobs.metadata.
    """
    export_format = job.get("format") or "dxf"
    logger.info(
        "[export_pipeline] running generation",
        job_id=job.get("id"),
        format=export_format,
        stage=PipelineStage.EXPORT_GENERATION.value,
    )
    # TODO: dispatch to dxf/ifc/dwg services by format
    await asyncio.sleep(0.5)
    return {
        "stage": PipelineStage.EXPORT_GENERATION.value,
        "format": export_format,
    }


async def run_preflight_gate(export_context: dict[str, Any]):
    """Run preflight; worker should fail job if can_proceed is False."""
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
