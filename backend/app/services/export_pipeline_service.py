"""
Export pipeline orchestration hooks — Kiruthika (Week 2).

Bridges Tazwar's worker to existing DXF/IFC/DWG paths. Generation is stubbed until
Yehor export_jobs + artifact handoff land; stage metadata is written for postflight.
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from uuid import UUID
from app.utils.storage_service import storage_service
from app.db.queries.file_queries import create_artifact_file

from app.core.export_stage_catalog import EXPORT_STAGE_CATALOG
from app.schemas.export_contracts import PipelineStage
from app.services.export_validation_service import run_preflight, run_postflight
from app.utils.logger import logger


async def run_export_generation(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    PROCESSING stage: formats exported and persisted into regional storage.
    Returns metadata patch including artifact_file_id for postflight verification.
    """
    export_format = job.get("format") or "dxf"
    project_id = job.get("project_id")
    job_id = job.get("id")
    user_id = job.get("requested_by") or "system"

    org_id_raw = job.get("organization_id")
    org_id: Optional[UUID] = None
    if org_id_raw:
        try:
            org_id = UUID(str(org_id_raw))
        except (ValueError, TypeError):
            org_id = None

    logger.info(
        "[export_pipeline] running generation",
        job_id=job_id,
        format=export_format,
        stage=PipelineStage.EXPORT_GENERATION.value,
    )

    # TODO: dispatch to dxf/ifc/dwg generator engines by format
    await asyncio.sleep(0.5)

    sample_bytes = b"SECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"export_{project_id}_{timestamp}.{export_format.lower()}"

    # Regional sovereign storage
    artifact_url = await storage_service.upload_cad_file(
        file_bytes=sample_bytes,
        project_id=project_id,
        user_id=user_id,
        file_extension=export_format,
        filename=filename,
        organization_id=org_id,
    )

    storage_path = (
        f"tenants/{org_id}/cad/{project_id}/{filename}"
        if org_id
        else f"{user_id}/{project_id}/{filename}"
    )

    # Persist artifact file record
    artifact_row = await create_artifact_file(
        file_data={
            "project_id": project_id,
            "job_id": job_id,
            "path": storage_path,
            "file_type": export_format.lower(),
            "size_bytes": len(sample_bytes),
            "name": filename,
        },
        user_id=user_id,
        organization_id=org_id,
    )
    artifact_file_id = artifact_row.get("id") if artifact_row else None

    # Link artifact_file_id on job root context for Kiruthika's run_postflight
    if artifact_file_id:
        job["artifact_file_id"] = artifact_file_id

    return {
        "stage": PipelineStage.ARTIFACT_STORAGE.value,
        "format": export_format,
        "artifact_file_id": artifact_file_id,
        "artifact_url": artifact_url,
    }


async def run_preflight_gate(export_context: Dict[str, Any]):
    """Run preflight; worker should fail job if can_proceed is False."""
    report = await run_preflight(export_context)
    if not report.can_proceed:
        logger.warning(
            "[export_pipeline] preflight blocked",
            export_id=export_context.get("id"),
            issue_count=len(report.issues),
        )
    return report


async def run_postflight_gate(export_context: Dict[str, Any]):
    """Run postflight; worker uses passed/requires_review for status routing."""
    return await run_postflight(export_context)


def get_stage_catalog():
    return EXPORT_STAGE_CATALOG
