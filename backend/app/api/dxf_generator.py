"""
DXF Generator API endpoints for converting CAD instructions to DXF files
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.queries.project_queries import update_project
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.models.project_model import ProjectUpdate
from app.schemas.parser import (
    CADFileType,
    ParsingRequest,
)
from app.services.supabase_service import supabase_service
from app.utils.storage_service import storage_service

logger = logging.getLogger(__name__)


def _cleanup_file(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.warning("Unable to remove temporary file %s: %s", path, exc)


def _cleanup_directory(path: str) -> None:
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.warning("Unable to remove temporary directory %s: %s", path, exc)


async def _resolve_project_org_id(project_id: str | None) -> UUID | None:
    """Resolve enterprise workspace_id (organization_id) for a project."""
    if not project_id:
        return None
    try:
        central_client = supabase_service.client or db
        proj_data = await run_in_threadpool(
            lambda: central_client.table("projects")
            .select("workspace_id")
            .eq("id", project_id)
            .maybe_single()
            .execute()
        )
        if proj_data and proj_data.data and proj_data.data.get("workspace_id"):
            return UUID(str(proj_data.data["workspace_id"]))
    except (ValueError, TypeError, Exception):
        return None
    return None


# Import services with error handling
try:
    from app.services.gemini_service import gemini_service
except ImportError as e:
    logger.warning(f"Failed to import gemini_service: {e}.")
    gemini_service = None

try:
    from app.services.gemini_transcription_service import gemini_transcription_service
except ImportError as e:
    logger.warning(f"Failed to import gemini_transcription_service: {e}.")
    gemini_transcription_service = None

try:
    from app.services.cadllm_service import cadllm_service
except ImportError as e:
    logger.warning(f"Failed to import cadllm_service: {e}.")
    cadllm_service = None

try:
    from app.services.external_dxf_service import external_dxf_service
except ImportError as e:
    logger.warning(f"Failed to import external_dxf_service: {e}.")
    external_dxf_service = None

try:
    from app.services.local_dxf_service import local_dxf_service
except ImportError as e:
    logger.warning(f"Failed to import local_dxf_service: {e}.")
    local_dxf_service = None

try:
    from app.services.dwg_converter_service import dwg_converter_service
except ImportError as e:
    logger.warning(f"Failed to import dwg_converter_service: {e}.")
    dwg_converter_service = None

router = APIRouter()


@router.post("/generate-from-audio")
async def generate_dxf_from_audio(
    file: UploadFile = File(...),
    language: str | None = Query("en", description="Language code (ISO 639-1)"),
    units: str | None = Query(
        "inches", description="Units for measurements (inches, feet, mm)"
    ),
):
    """
    Generate DXF file related to audio input using the Unified Flow:
    Audio -> Gemini Transcribe -> CADLLM Prompt Enhancement -> Gemini Validate & Fix -> Gemini Image -> API2Convert -> DXF
    """
    if not gemini_transcription_service:
        raise HTTPException(
            status_code=503, detail="Gemini transcription service unavailable."
        )
    if not cadllm_service:
        raise HTTPException(status_code=503, detail="CADLLM service unavailable.")
    if not gemini_service:
        raise HTTPException(status_code=503, detail="Gemini service unavailable.")
    if settings.DXF_GENERATION_METHOD == "API" and not external_dxf_service:
        raise HTTPException(status_code=503, detail="External DXF service unavailable.")
    if settings.DXF_GENERATION_METHOD == "LOCAL" and not local_dxf_service:
        raise HTTPException(status_code=503, detail="Local DXF service unavailable.")

    try:
        # 1. Transcribe
        logger.info("Transcribing audio file with Gemini...")
        transcribed_text, _, _ = await gemini_transcription_service.transcribe_file(
            file_input=file,
            filename=file.filename or "audio",
            language=language,
        )

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Transcription failed/empty.")

        logger.info(f"Transcribed Text: {transcribed_text}")

        # 2. Enhance Prompt (CADLLM)
        logger.info("Enhancing prompt with CADLLM...")
        enhanced_prompt = await cadllm_service.enhance_prompt(transcribed_text)
        logger.info(f"Enhanced Prompt: {enhanced_prompt}")

        # 3. Generate Image (Gemini)
        logger.info("Generating Image with Gemini...")
        image_url = await gemini_service.generate_image(
            enhanced_prompt, original_prompt=transcribed_text
        )

        if "placehold.co" in image_url:
            raise HTTPException(status_code=500, detail="Image generation failed.")

        # 4. Convert to DXF (Api2Convert)
        if settings.DXF_GENERATION_METHOD == "LOCAL":
            logger.info("Converting Image to DXF (Local - Potrace)...")
            dxf_path = await local_dxf_service.convert_to_dxf(image_url)
        else:
            logger.info("Converting Image to DXF (API)...")
            dxf_path = await external_dxf_service.convert_to_dxf(image_url)

        # 5. Return File
        dxf_bytes = await asyncio.to_thread(Path(dxf_path).read_bytes)

        # Cleanup temp file
        _cleanup_file(dxf_path)

        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_audio.dxf"'
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unified audio flow failed")
        raise HTTPException(
            status_code=500, detail="An error occurred during DXF generation."
        )


@router.post("/generate-from-text")
async def generate_dxf_from_text(
    request: ParsingRequest = Body(...),
    use_json_pipeline: bool | None = Query(
        True, description="Ignored. Uses Unified Flow."
    ),
):
    """
    Generate DXF file from text input using the Unified Flow:
    Text -> CADLLM Prompt Enhancement -> Gemini Validate & Fix -> Gemini Image -> API2Convert -> DXF
    """
    if not cadllm_service:
        raise HTTPException(status_code=503, detail="CADLLM service unavailable.")
    if not gemini_service:
        raise HTTPException(status_code=503, detail="Gemini service unavailable.")
    if settings.DXF_GENERATION_METHOD == "API" and not external_dxf_service:
        raise HTTPException(status_code=503, detail="External DXF service unavailable.")
    if settings.DXF_GENERATION_METHOD == "LOCAL" and not local_dxf_service:
        raise HTTPException(status_code=503, detail="Local DXF service unavailable.")

    try:
        # 1. Enhance Prompt (CADLLM)
        logger.info("Enhancing prompt with CADLLM...")
        enhanced_prompt = await cadllm_service.enhance_prompt(request.text)
        logger.info(f"Enhanced Prompt: {enhanced_prompt}")

        # 2. Generate Image (Gemini)
        logger.info("Generating Image with Gemini...")
        image_url = await gemini_service.generate_image(
            enhanced_prompt, original_prompt=request.text
        )

        if "placehold.co" in image_url:
            raise HTTPException(status_code=500, detail="Image generation failed.")

        # 3. Convert to DXF (Api2Convert)
        if settings.DXF_GENERATION_METHOD == "LOCAL":
            logger.info("Converting Image to DXF (Local - Potrace)...")
            dxf_path = await local_dxf_service.convert_to_dxf(image_url)
        else:
            logger.info("Converting Image to DXF (API)...")
            dxf_path = await external_dxf_service.convert_to_dxf(image_url)

        # 4. Return File
        dxf_bytes = await asyncio.to_thread(Path(dxf_path).read_bytes)

        # Cleanup temp file
        _cleanup_file(dxf_path)

        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_text.dxf"'
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unified text flow failed")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during text-to-DXF generation.",
        )


@router.post("/generate-and-store")
async def generate_and_store_dxf(
    request: ParsingRequest = Body(...),
    project_id: str | None = Body(
        None, description="Project ID to associate the DXF file with"
    ),
    user: dict = Depends(require_auth),
):
    """Generate DXF/DWG from text and optionally store on project."""
    if not cadllm_service:
        raise HTTPException(status_code=503, detail="CADLLM service unavailable.")
    if not gemini_service:
        raise HTTPException(status_code=503, detail="Gemini service unavailable.")
    if settings.DXF_GENERATION_METHOD == "API" and not external_dxf_service:
        raise HTTPException(status_code=503, detail="External DXF service unavailable.")
    if settings.DXF_GENERATION_METHOD == "LOCAL" and not local_dxf_service:
        raise HTTPException(status_code=503, detail="Local DXF service unavailable.")

    try:
        # 1. Enhance Prompt (CADLLM)
        enhanced_prompt = await cadllm_service.enhance_prompt(request.text)

        # 2. Generate Image (Gemini)
        image_url = await gemini_service.generate_image(
            enhanced_prompt, original_prompt=request.text
        )

        if "placehold.co" in image_url:
            raise HTTPException(status_code=500, detail="Image generation failed.")

        if settings.DXF_GENERATION_METHOD == "LOCAL":
            logger.info("Converting Image to DXF (Local - Potrace)...")
            dxf_path = await local_dxf_service.convert_to_dxf(image_url)
        else:
            logger.info("Converting Image to DXF (API)...")
            dxf_path = await external_dxf_service.convert_to_dxf(image_url)

        dxf_bytes = await asyncio.to_thread(Path(dxf_path).read_bytes)

        requested_type = request.file_type or CADFileType.DXF
        dwg_bytes = None
        dwg_temp_dir = None
        if requested_type == CADFileType.DWG:
            if not dwg_converter_service:
                raise HTTPException(
                    status_code=503, detail="DWG converter service unavailable."
                )
            try:
                convert_result = dwg_converter_service.convert_dxf_path_to_dwg(dxf_path)
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))

            dwg_temp_dir = convert_result.work_dir
            dwg_bytes = await asyncio.to_thread(
                Path(convert_result.dwg_path).read_bytes
            )

        _cleanup_file(dxf_path)

        if dwg_temp_dir:
            _cleanup_directory(dwg_temp_dir)

        dxf_url = None
        dwg_url = None
        image_public_url = image_url
        if project_id:
            user_id = user.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found")

            org_id = await _resolve_project_org_id(project_id)

            # Pass organization_id to target regional bucket
            dxf_url = await storage_service.upload_cad_file(
                file_bytes=dxf_bytes,
                project_id=project_id,
                user_id=user_id,
                file_extension="dxf",
                organization_id=org_id,
            )

            if dwg_bytes:
                dwg_url = await storage_service.upload_cad_file(
                    file_bytes=dwg_bytes,
                    project_id=project_id,
                    user_id=user_id,
                    file_extension="dwg",
                    organization_id=org_id,
                )

            update_payload = ProjectUpdate(
                image_url=image_public_url,
                dxf_url=dxf_url,
                dwg_url=dwg_url,
            )
            if dxf_url or dwg_url or image_public_url:
                await update_project(
                    project_id=project_id,
                    update_data=update_payload,
                    user=user,
                )
                logger.info("✅ CAD files stored and project updated: %s", project_id)

        return {
            "status": "success",
            "message": "Design file generated successfully",
            "file_type": (
                requested_type.value
                if isinstance(requested_type, CADFileType)
                else str(requested_type)
            ),
            "image_url": image_public_url,
            "dxf_url": dxf_url,
            "dwg_url": dwg_url,
            "download_url": (
                f"/api/v1/dxf/download?project_id={project_id}&file_type="
                f"{'dwg' if requested_type == CADFileType.DWG else 'dxf'}"
            )
            if project_id
            else None,
            "file_size": (
                len(dwg_bytes)
                if requested_type == CADFileType.DWG and dwg_bytes
                else len(dxf_bytes)
            ),
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("DXF generation and storage error")
        raise HTTPException(
            status_code=500,
            detail="DXF generation and storage failed due to an internal error.",
        )


@router.get("/download")
async def download_project_dxf(
    project_id: str = Query(..., description="Project ID to download DXF file from"),
    file_type: CADFileType = Query(
        CADFileType.DXF, description="File type to download: dxf|dwg"
    ),
    user: dict = Depends(require_auth),
):
    """
    Download DXF/DWG file for a project from Supabase Storage.
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")

        ext = "dwg" if file_type == CADFileType.DWG else "dxf"
        org_id = await _resolve_project_org_id(project_id)

        file_bytes = await storage_service.download_cad_file(
            project_id=project_id,
            user_id=user_id,
            file_extension=ext,
            organization_id=org_id,
        )

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"{ext.upper()} file not found for this project",
            )

        media_type = "application/acad" if ext == "dwg" else "application/dxf"
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="project_{project_id}.{ext}"'
            },
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("DXF download error")
        raise HTTPException(
            status_code=500,
            detail="DXF download failed due to an internal error.",
        )