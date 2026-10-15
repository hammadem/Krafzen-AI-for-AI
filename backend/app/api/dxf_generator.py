"""
DXF Generator API endpoints for converting CAD instructions to DXF files
"""

import logging
import os
import shutil

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

from app.db.queries.project_queries import update_project
from app.middlewares.auth import require_auth
from app.models.project_model import ProjectUpdate
from app.schemas.parser import (
    CADFileType,
    ParsingRequest,
)
from app.utils.storage_service import storage_service

logger = logging.getLogger(__name__)

# Import services with error handling


try:
    from app.services.gemini_service import gemini_service
except Exception as e:
    logger.warning(f"Failed to import gemini_service: {e}.")
    gemini_service = None

try:
    from app.services.gemini_transcription_service import gemini_transcription_service
except Exception as e:
    logger.warning(f"Failed to import gemini_transcription_service: {e}.")
    gemini_transcription_service = None

try:
    from app.services.cadllm_service import cadllm_service
except Exception as e:
    logger.warning(f"Failed to import cadllm_service: {e}.")
    cadllm_service = None

try:
    from app.services.external_dxf_service import external_dxf_service
except Exception as e:
    logger.warning(f"Failed to import external_dxf_service: {e}.")
    external_dxf_service = None

try:
    from app.services.local_dxf_service import local_dxf_service
except Exception as e:
    logger.warning(f"Failed to import local_dxf_service: {e}.")
    local_dxf_service = None

try:
    from app.services.dwg_converter_service import dwg_converter_service
except Exception as e:
    logger.warning(f"Failed to import dwg_converter_service: {e}.")
    dwg_converter_service = None

from app.core.config import settings

router = APIRouter()

@router.post("/generate-from-audio")
async def generate_dxf_from_audio(
    file: UploadFile = File(...),
    language: str | None = Query("en", description="Language code (ISO 639-1)"),
    units: str | None = Query("inches", description="Units for measurements (inches, feet, mm)")
):
    """
    Generate DXF file related to audio input using the Unified Flow:
    Audio -> Gemini Transcribe -> CADLLM Prompt Enhancement -> Gemini Validate & Fix -> Gemini Image -> API2Convert -> DXF
    """
    if not gemini_transcription_service:
        raise HTTPException(status_code=503, detail="Gemini transcription service unavailable.")
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
            language=language
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
        image_url = await gemini_service.generate_image(enhanced_prompt, original_prompt=transcribed_text)
        
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
        with open(dxf_path, 'rb') as f:
            dxf_bytes = f.read()
            
        # Cleanup temp file
        try:
            import os
            os.unlink(dxf_path)
        except:
            pass
            
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_audio.dxf"'
            }
        )
        
    except Exception as e:
        logger.error(f"Unified audio flow failed: {e}", exc_info=True)
        # Return generic error
        raise HTTPException(status_code=500, detail="An error occurred during DXF generation.")


@router.post("/generate-from-text")
async def generate_dxf_from_text(
    request: ParsingRequest = Body(...),
    use_json_pipeline: bool | None = Query(True, description="Ignored. Uses Unified Flow.")
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
        image_url = await gemini_service.generate_image(enhanced_prompt, original_prompt=request.text)
        
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
        with open(dxf_path, 'rb') as f:
            dxf_bytes = f.read()
            
        # Cleanup temp file
        try:
            import os
            os.unlink(dxf_path)
        except:
            pass
            
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_text.dxf"'
            }
        )
        
    except Exception as e:
        logger.error(f"Unified text flow failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during text-to-DXF generation.")


@router.post("/generate-and-store")
async def generate_and_store_dxf(
    request: ParsingRequest = Body(...),
    project_id: str | None = Body(None, description="Project ID to associate the DXF file with"),
    user: dict = Depends(require_auth)
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
        image_url = await gemini_service.generate_image(enhanced_prompt, original_prompt=request.text)
        
        if "placehold.co" in image_url:
            raise HTTPException(status_code=500, detail="Image generation failed.")
        
        if settings.DXF_GENERATION_METHOD == "LOCAL":
            logger.info("Converting Image to DXF (Local - Potrace)...")
            dxf_path = await local_dxf_service.convert_to_dxf(image_url)
        else:
            logger.info("Converting Image to DXF (API)...")
            dxf_path = await external_dxf_service.convert_to_dxf(image_url)

        with open(dxf_path, "rb") as f:
            dxf_bytes = f.read()

        requested_type = request.file_type or CADFileType.DXF
        dwg_bytes = None
        dwg_temp_dir = None
        if requested_type == CADFileType.DWG:
            if not dwg_converter_service:
                raise HTTPException(status_code=503, detail="DWG converter service unavailable.")
            try:
                convert_result = dwg_converter_service.convert_dxf_path_to_dwg(dxf_path)
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))

            dwg_temp_dir = convert_result.work_dir
            with open(convert_result.dwg_path, "rb") as f:
                dwg_bytes = f.read()

        try:
            os.unlink(dxf_path)
        except Exception:
            pass

        if dwg_temp_dir:
            try:
                shutil.rmtree(dwg_temp_dir, ignore_errors=True)
            except Exception:
                pass

        dxf_url = None
        dwg_url = None
        image_public_url = image_url
        if project_id:
            user_id = user.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found")

            dxf_url = await storage_service.upload_cad_file(
                file_bytes=dxf_bytes,
                project_id=project_id,
                user_id=user_id,
                file_extension="dxf",
            )

            if dwg_bytes:
                dwg_url = await storage_service.upload_cad_file(
                    file_bytes=dwg_bytes,
                    project_id=project_id,
                    user_id=user_id,
                    file_extension="dwg",
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
            "file_type": requested_type.value if isinstance(requested_type, CADFileType) else str(requested_type),
            "image_url": image_public_url,
            "dxf_url": dxf_url,
            "dwg_url": dwg_url,
            "download_url": (
                f"/api/v1/dxf/download?project_id={project_id}&file_type="
                f"{'dwg' if requested_type == CADFileType.DWG else 'dxf'}"
            ) if project_id else None,
            "file_size": len(dwg_bytes) if requested_type == CADFileType.DWG and dwg_bytes else len(dxf_bytes),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation and storage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="DXF generation and storage failed due to an internal error."
        )


@router.get("/download")
async def download_project_dxf(
    project_id: str = Query(..., description="Project ID to download DXF file from"),
    file_type: CADFileType = Query(CADFileType.DXF, description="File type to download: dxf|dwg"),
    user: dict = Depends(require_auth)
):
    """
    Download DXF file for a project from Supabase Storage
    
    Args:
        project_id: Project ID
        user: Authenticated user
    
    Returns:
        DXF file as binary response
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        ext = "dwg" if file_type == CADFileType.DWG else "dxf"
        file_bytes = await storage_service.download_cad_file(project_id=project_id, user_id=user_id, file_extension=ext)

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
    except Exception as e:
        logger.error(f"DXF download error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="DXF download failed due to an internal error."
        )



