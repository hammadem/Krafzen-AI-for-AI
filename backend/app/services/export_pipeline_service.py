"""Project-backed DXF/DWG and visual-reference PDF export pipeline.

Current implementation traces the persisted project image to vectors. It does NOT
reconstruct dimensional CAD primitives or BIM geometry. IFC/Revit exports are not
implemented and are explicitly rejected rather than uploading sample content.
"""

import asyncio
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import ezdxf
from fastapi.concurrency import run_in_threadpool

from app.core.export_stage_catalog import EXPORT_STAGE_CATALOG
from app.db.queries.export_queries import update_export_status
from app.db.queries.file_queries import create_artifact_file
from app.db.supabase_client import db
from app.schemas.export_contracts import PipelineStage
from app.services.dwg_converter_service import dwg_converter_service
from app.services.export_validation_service import run_postflight, run_preflight
from app.services.local_dxf_service import local_dxf_service
from app.services.reference_pdf_service import create_reference_pdf
from app.utils.logger import logger
from app.utils.storage_service import MAX_FILE_SIZES_BYTES, storage_service

# Only inline images persisted on the server are accepted. Never fetch arbitrary
# project image URLs using worker credentials (SSRF and cross-region exposure).
_IMAGE_DATA_URI = re.compile(r"^data:image/(?:png|jpeg|webp);base64,", re.IGNORECASE)
_MAX_INLINE_IMAGE_LENGTH = 25 * 1024 * 1024


async def _load_source_project(project_id: str, user_id: str) -> dict[str, Any]:
    """Load the persisted project and verify it belongs to the export requester."""
    response = await run_in_threadpool(
        lambda: db.table("projects")
        .select("id,user_id,image_url,workspace_id")
        .eq("id", project_id)
        .maybe_single()
        .execute()
    )
    project = response.data if response else None
    if not isinstance(project, dict):
        raise RuntimeError("Export source project does not exist")
    if str(project.get("user_id") or "") != user_id:
        raise PermissionError("Export requester does not own the source project")
    return project


def _source_image(project: dict[str, Any]) -> str:
    image = project.get("image_url")
    if not isinstance(image, str) or not _IMAGE_DATA_URI.match(image):
        raise RuntimeError(
            "The project has no supported stored image. "
            "Export requires a PNG/JPEG/WebP data URI; remote image URLs are not fetched."
        )
    if len(image) > _MAX_INLINE_IMAGE_LENGTH:
        raise RuntimeError("Project source image exceeds the export limit")
    return image


def _validate_dxf(path: str) -> None:
    """Reject empty, truncated or unreadable DXF output."""
    doc = ezdxf.readfile(path)
    if not any(True for _ in doc.modelspace()):
        raise RuntimeError("DXF conversion produced no drawable entities")


def _read_bounded(path: str, export_format: str) -> bytes:
    max_size = MAX_FILE_SIZES_BYTES[export_format]
    size = os.path.getsize(path)
    if size <= 0 or size > max_size:
        raise RuntimeError("Generated artifact has an invalid file size")
    data = Path(path).read_bytes()
    if export_format == "dwg" and (len(data) < 256 or not data.startswith(b"AC10")):
        raise RuntimeError("DWG converter output has no valid AutoCAD header")
    return data


async def _generate_file(image_source: str, export_format: str) -> bytes:
    """Generate a real reference PDF or trace image to DXF/DWG via ODA."""
    if export_format == "pdf":
        return await asyncio.to_thread(create_reference_pdf, image_source)
    dxf_path: str | None = None
    work_dir: str | None = None
    try:
        dxf_path = await local_dxf_service.convert_to_dxf(image_source)
        await asyncio.to_thread(_validate_dxf, dxf_path)
        if export_format == "dxf":
            return await asyncio.to_thread(_read_bounded, dxf_path, "dxf")

        result = await asyncio.to_thread(
            dwg_converter_service.convert_dxf_path_to_dwg, dxf_path
        )
        work_dir = result.work_dir
        return await asyncio.to_thread(_read_bounded, result.dwg_path, "dwg")
    finally:
        if dxf_path:
            try:
                await asyncio.to_thread(os.unlink, dxf_path)
            except FileNotFoundError:
                pass
        if work_dir:
            await asyncio.to_thread(shutil.rmtree, work_dir, ignore_errors=True)


async def run_export_generation(job: dict[str, Any]) -> dict[str, Any]:
    """Generate a genuine project-backed file and persist the artifact reference."""
    export_format = str(job.get("format") or "").lower()
    if export_format not in ("dxf", "dwg", "pdf"):
        raise RuntimeError(
            f"Export format '{export_format}' has no implemented generator. "
            "IFC and Revit packages must not contain placeholder bytes."
        )

    project_id = str(job.get("project_id") or "")
    job_id = str(job.get("id") or "")
    user_id = str(job.get("requested_by") or "")
    if not project_id or not job_id or not user_id:
        raise RuntimeError("Export requires project_id, job id and requested_by")

    raw_org = job.get("organization_id")
    try:
        org_id = UUID(str(raw_org)) if raw_org else None
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Invalid export organization ID") from exc

    # Regional metadata/files still use central persistence elsewhere in this
    # application. Do not process sovereign artifacts until fully regionalized.
    if str(job.get("region_code") or "global").lower() != "global":
        raise RuntimeError(
            "Sovereign exports are unavailable until regional artifact metadata "
            "persistence and source reads are verified."
        )

    project = await _load_source_project(project_id, user_id)
    workspace = project.get("workspace_id")
    if workspace and (not org_id or str(workspace) != str(org_id)):
        raise PermissionError("Export organization does not match source project")
    if org_id and not workspace:
        raise PermissionError("Export organization is not linked to source project")

    source_image = _source_image(project)
    logger.info(
        "[export_pipeline] generating real artifact",
        job_id=job_id,
        format=export_format,
        stage=PipelineStage.EXPORT_GENERATION.value,
    )
    file_bytes = await _generate_file(source_image, export_format)
    filename = (
        f"export_{project_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid4().hex[:12]}.{export_format}"
    )

    # Do not register or complete an export unless the upload succeeded.
    artifact_url = await storage_service.upload_cad_file(
        file_bytes=file_bytes,
        project_id=project_id,
        user_id=user_id,
        file_extension=export_format,
        filename=filename,
        organization_id=org_id,
    )
    if not artifact_url:
        raise RuntimeError("Artifact upload did not return a storage URL")

    _, bucket_name, _ = storage_service.resolve_target_bucket_and_client(org_id)
    storage_path = (
        f"tenants/{org_id}/cad/{project_id}/{filename}"
        if org_id else f"{user_id}/{project_id}/{filename}"
    )
    payload: dict[str, Any] = {
        "bucket": bucket_name,
        "project_id": project_id,
        "job_id": job_id,
        "path": storage_path,
        "file_type": export_format,
        "mime_type": storage_service._content_type_for_extension(export_format),
        "size_bytes": len(file_bytes),
        "name": filename,
    }
    artifact = await create_artifact_file(
        file_data=payload, user_id=user_id, organization_id=org_id
    )
    artifact_id = artifact.get("id") if isinstance(artifact, dict) else None
    if not artifact_id:
        raise RuntimeError("Artifact file record could not be persisted")

    patch = {
        "artifact_file_id": artifact_id,
        "bucket": bucket_name,
        "file_path": storage_path,
        "metadata": {
            **(job.get("metadata") or {}),
            "stage": PipelineStage.ARTIFACT_STORAGE.value,
            "generation_method": ("project_raster_reference_pdf" if export_format == "pdf" else "raster_vector_trace"),
            "engineering_accuracy_verified": False,
        },
    }
    saved = await update_export_status(job_id, patch, user_id)
    if not saved or str(saved.get("artifact_file_id") or "") != str(artifact_id):
        raise RuntimeError("Artifact reference was not persisted on the export job")

    job["artifact_file_id"] = artifact_id
    job["metadata"] = patch["metadata"]
    return {
        "stage": PipelineStage.ARTIFACT_STORAGE.value,
        "format": export_format,
        "artifact_file_id": artifact_id,
        "artifact_url": artifact_url,
        "bucket": bucket_name,
        "file_path": storage_path,
        "generation_method": ("project_raster_reference_pdf" if export_format == "pdf" else "raster_vector_trace"),
        "engineering_accuracy_verified": False,
    }


async def run_preflight_gate(export_context: dict[str, Any]):
    """Run preflight; worker must fail a job if can_proceed is False."""
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
