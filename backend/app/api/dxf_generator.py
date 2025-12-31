"""
DXF Generator API endpoints for converting CAD instructions to DXF files
"""

from fastapi import APIRouter, HTTPException, Body, Response, Depends, Query, UploadFile, File
from typing import Optional, List
from app.schemas.parser import (
    ParsingRequest,
    ParsingResponse,
    ParsedInstruction,
    CADFileType
)
from typing import Dict, Any
from datetime import datetime
import logging
from app.middlewares.auth import require_auth
from app.utils.storage_service import storage_service
from app.db.queries.project_queries import update_project
from app.models.project_model import ProjectUpdate

logger = logging.getLogger(__name__)

# Import services with error handling
try:
    from app.services.dxf_generator_service import dxf_generator_service
except Exception as e:
    logger.warning(f"Failed to import dxf_generator_service: {e}. DXF endpoints will return 503.")
    dxf_generator_service = None

try:
    from app.services.gpt_parser_service import gpt_parser_service
except Exception as e:
    logger.warning(f"Failed to import gpt_parser_service: {e}.")
    gpt_parser_service = None

try:
    from app.services.gemini_transcription_service import gemini_transcription_service
except Exception as e:
    logger.warning(f"Failed to import gemini_transcription_service: {e}.")
    gemini_transcription_service = None

try:
    from app.services.cadllm_service import cadllm_service
except Exception as e:
    logger.warning(f"Failed to import cadllm_service: {e}. CADLLM endpoints will return 503.")
    cadllm_service = None

router = APIRouter()


@router.post("/generate")
async def generate_dxf_from_instructions(
    instructions: List[ParsedInstruction] = Body(..., description="Parsed CAD instructions"),
    filename: Optional[str] = Body(None, description="Optional filename for the DXF file")
):
    """
    Generate DXF file from parsed CAD instructions
    
    Args:
        instructions: List of parsed CAD instructions
        filename: Optional filename for the DXF file
    
    Returns:
        DXF file as binary response
    """
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        # Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename=filename
        )
        
        # Validate the generated DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
            # Still return the file, but log the warning
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename or "output.dxf"}"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"DXF generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/generate-from-json")
async def generate_dxf_from_json(
    json_data: Dict[str, Any] = Body(..., description="Structured JSON with entities and coordinates")
):
    """
    Generate DXF file from structured JSON format.
    
    This endpoint accepts machine-readable JSON with exact coordinates,
    providing precise control over the generated drawing.
    
    Args:
        json_data: JSON object with entities, units, and format
    
    Returns:
        DXF file as binary response
    """
    """
    Generate DXF file from structured JSON format
    
    Args:
        json_data: JSON object with entities, units, and format
    
    Returns:
        DXF file as binary response
    """
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        from app.services.json_instruction_parser import json_instruction_parser
        
        # Parse JSON to instructions
        instructions = json_instruction_parser.parse_json(json_data)
        
        if not instructions:
            raise HTTPException(
                status_code=400,
                detail="No valid instructions parsed from JSON"
            )
        
        # Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename=None
        )
        
        # Validate the generated DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_json.dxf"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation from JSON error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/generate-from-text-via-json")
async def generate_dxf_from_text_via_json(
    request: ParsingRequest = Body(...)
):
    """
    Generate DXF file from text by first converting to JSON format (RECOMMENDED).
    
    This two-stage approach (Text → JSON → DXF) provides better accuracy
    than direct text parsing by ensuring all elements are captured in structured format.
    
    Args:
        request: ParsingRequest with text and file type
    
    Returns:
        DXF file as binary response
    """
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        from app.services.text_to_json_converter import text_to_json_converter
        from app.services.json_instruction_parser import json_instruction_parser
        
        if not text_to_json_converter:
            raise HTTPException(
                status_code=503,
                detail="Text to JSON converter is not configured. Please check OPENAI_API_KEY."
            )
        
        # Step 1: Convert text to JSON
        logger.info("Converting text to structured JSON format...")
        json_data = await text_to_json_converter.convert_text_to_json(
            text=request.text,
            units="inches"  # Default, can be made configurable
        )
        
        # Step 2: Parse JSON to instructions
        instructions = json_instruction_parser.parse_json(json_data)
        
        if not instructions:
            raise HTTPException(
                status_code=400,
                detail="No valid instructions parsed from JSON"
            )
        
        # Step 3: Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename=None
        )
        
        # Validate the generated DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_from_text_via_json.dxf"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation from text via JSON error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/generate-from-audio")
async def generate_dxf_from_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Query("en", description="Language code (ISO 639-1)"),
    units: Optional[str] = Query("inches", description="Units for measurements (inches, feet, mm)")
):
    """
    Generate DXF file directly from audio using JSON pipeline (RECOMMENDED).
    
    This endpoint uses Option 2 pipeline: Audio → Transcription → JSON → DXF
    for better accuracy and precision.
    
    Args:
        file: Audio file (mp3, wav, m4a, ogg, flac, webm)
        language: Language code (default: en, use "auto" for auto-detection)
        units: Units for measurements (default: inches)
    
    Returns:
        DXF file as binary response
    """
    if not gemini_transcription_service:
        raise HTTPException(
            status_code=503,
            detail="Gemini transcription service is not configured. Please check GEMINI_API_KEY."
        )
    
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        from app.services.text_to_json_converter import text_to_json_converter
        from app.services.json_instruction_parser import json_instruction_parser
        
        if not text_to_json_converter:
            raise HTTPException(
                status_code=503,
                detail="Text to JSON converter is not configured. Please check OPENAI_API_KEY."
            )
        
        # Step 1: Transcribe audio
        logger.info("Transcribing audio file with Gemini...")
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        transcribed_text, detected_language, duration = await gemini_transcription_service.transcribe_file(
            file_content=file_content,
            filename=file.filename or "audio",
            language=language
        )
        
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Transcription returned empty text")
        
        logger.info(f"Transcription successful: {len(transcribed_text)} characters")
        
        # Step 2: Convert text to JSON
        logger.info("Converting text to structured JSON format...")
        json_data = await text_to_json_converter.convert_text_to_json(
            text=transcribed_text,
            units=units
        )
        
        # Step 3: Parse JSON to instructions
        instructions = json_instruction_parser.parse_json(json_data)
        
        if not instructions:
            raise HTTPException(
                status_code=400,
                detail="No valid instructions parsed from JSON"
            )
        
        logger.info(f"Parsed {len(instructions)} instructions from JSON")
        
        # Step 4: Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename=None
        )
        
        # Validate the generated DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
        
        # Generate filename from audio file
        audio_name = (file.filename or "audio").rsplit('.', 1)[0]
        safe_name = audio_name.replace(" ", "_").replace("/", "_")
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.dxf"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation from audio error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/generate-from-text")
async def generate_dxf_from_text(
    request: ParsingRequest = Body(...),
    use_json_pipeline: Optional[bool] = Query(True, description="Use JSON pipeline (Option 2) for better accuracy. Set to False for direct parsing (Option 1).")
):
    """
    Parse text and generate DXF file.
    
    By default, uses JSON pipeline (Option 2) for better accuracy.
    Set use_json_pipeline=False to use direct parsing (Option 1).
    
    Args:
        request: ParsingRequest with text and file type
        use_json_pipeline: Use JSON pipeline (default: True, recommended)
    
    Returns:
        DXF file as binary response
    """
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        if use_json_pipeline:
            # Use JSON pipeline (Option 2) - RECOMMENDED
            from app.services.text_to_json_converter import text_to_json_converter
            from app.services.json_instruction_parser import json_instruction_parser
            
            if not text_to_json_converter:
                raise HTTPException(
                    status_code=503,
                    detail="Text to JSON converter is not configured. Please check OPENAI_API_KEY."
                )
            
            # Step 1: Convert text to JSON
            logger.info("Converting text to structured JSON format (Option 2)...")
            json_data = await text_to_json_converter.convert_text_to_json(
                text=request.text,
                units="inches"  # Default, can be made configurable
            )
            
            # Step 2: Parse JSON to instructions
            instructions = json_instruction_parser.parse_json(json_data)
            
            if not instructions:
                raise HTTPException(
                    status_code=400,
                    detail="No valid instructions parsed from JSON"
                )
        else:
            # Use direct parsing (Option 1)
            if not gpt_parser_service:
                raise HTTPException(
                    status_code=503,
                    detail="GPT-4 parser service is not configured. Please check OPENAI_API_KEY."
                )
            
            logger.info("Parsing text directly (Option 1)...")
            instructions, raw_response = await gpt_parser_service.parse_text(
                text=request.text,
                file_type=CADFileType.DXF,  # Force DXF for generation
                additional_context=request.additional_context
            )
            
            if not instructions:
                raise HTTPException(
                    status_code=400,
                    detail="No valid instructions parsed from text"
                )
        
        # Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename=None
        )
        
        # Validate the generated DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated.dxf"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation from text error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/validate")
async def validate_dxf_file(
    dxf_file: bytes = Body(..., description="DXF file content as bytes")
):
    """
    Validate DXF file format
    
    Args:
        dxf_file: DXF file content as bytes
    
    Returns:
        Validation result with status and message
    """
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_file)
        
        return {
            "status": "valid" if is_valid else "invalid",
            "message": error_msg if error_msg else "DXF file is valid",
            "is_valid": is_valid
        }
        
    except Exception as e:
        logger.error(f"DXF validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF validation failed: {str(e)}"
        )


@router.post("/generate-and-store")
async def generate_and_store_dxf(
    request: ParsingRequest = Body(...),
    project_id: Optional[str] = Body(None, description="Project ID to associate the DXF file with"),
    user: dict = Depends(require_auth)
):
    """
    Generate DXF file from text and store it in Supabase Storage
    
    Args:
        request: ParsingRequest with text and file type
        project_id: Optional project ID to link the DXF file
        user: Authenticated user
    
    Returns:
        JSON response with DXF file URL and download link
    """
    if not gpt_parser_service:
        raise HTTPException(
            status_code=503,
            detail="GPT-4 parser service is not configured."
        )
    
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available."
        )
    
    try:
        # Parse text
        instructions, raw_response = await gpt_parser_service.parse_text(
            text=request.text,
            file_type=CADFileType.DXF,
            additional_context=request.additional_context
        )
        
        if not instructions:
            raise HTTPException(
                status_code=400,
                detail="No valid instructions parsed from text"
            )
        
        # Generate DXF file
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        
        # Validate
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            logger.warning(f"Generated DXF validation warning: {error_msg}")
        
        # Upload to storage if project_id provided
        dxf_url = None
        if project_id:
            user_id = user.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found")
            
            dxf_url = await storage_service.upload_dxf_file(
                dxf_bytes=dxf_bytes,
                project_id=project_id,
                user_id=user_id
            )
            
            if dxf_url:
                # Update project with dxf_url
                await update_project(
                    project_id=project_id,
                    update_data=ProjectUpdate(dxf_url=dxf_url),
                    user=user
                )
                logger.info(f"✅ DXF file stored and project updated: {project_id}")
        
        # Return response with both download and URL
        return {
            "status": "success",
            "message": "DXF file generated successfully",
            "dxf_url": dxf_url,
            "download_url": f"/api/v1/dxf/download?project_id={project_id}" if project_id else None,
            "instructions_count": len(instructions),
            "file_size": len(dxf_bytes),
            "is_valid": is_valid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF generation and storage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation and storage failed: {str(e)}"
        )


@router.get("/download")
async def download_project_dxf(
    project_id: str = Query(..., description="Project ID to download DXF file from"),
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
        
        # Download from storage
        dxf_bytes = await storage_service.download_dxf_file(
            project_id=project_id,
            user_id=user_id
        )
        
        if not dxf_bytes:
            raise HTTPException(
                status_code=404,
                detail="DXF file not found for this project"
            )
        
        # Return file as download
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="project_{project_id}.dxf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DXF download error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF download failed: {str(e)}"
        )


@router.post("/generate-from-text-cadllm")
async def generate_dxf_from_text_cadllm(
    request: ParsingRequest = Body(...)
):
    """
    Generate DXF file from text using the fine-tuned CAD-LLM model (RECOMMENDED for 2D CAD).
    
    This endpoint uses the fine-tuned CAD-LLM model that outputs coordinates directly,
    which are then converted to DXF files. This is faster and more cost-effective than
    using GPT-4 for 2D CAD generation.
    
    Args:
        request: ParsingRequest with text and file type
    
    Returns:
        DXF file as binary response
    """
    if not cadllm_service:
        raise HTTPException(
            status_code=503,
            detail="CADLLM service is not configured. Please set HF_TOKEN and HF_MODEL_NAME or HF_ENDPOINT_URL."
        )
    
    if not cadllm_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="CADLLM service is not properly configured. Please check HF_TOKEN and model settings."
        )
    
    try:
        # Generate DXF using CADLLM
        logger.info(f"Generating DXF using CAD-LLM model for text: {request.text[:100]}...")
        dxf_bytes, error_msg = await cadllm_service.generate_dxf_from_text(
            text=request.text,
            filename=None
        )
        
        if error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"CADLLM generation failed: {error_msg}"
            )
        
        if not dxf_bytes:
            raise HTTPException(
                status_code=500,
                detail="CADLLM generation returned empty result"
            )
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": 'attachment; filename="generated_cadllm.dxf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CADLLM DXF generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )


@router.post("/generate-from-audio-cadllm")
async def generate_dxf_from_audio_cadllm(
    file: UploadFile = File(...),
    language: Optional[str] = Query("en", description="Language code (ISO 639-1)"),
):
    """
    Generate DXF file from audio using CAD-LLM model (RECOMMENDED for 2D CAD).
    
    This endpoint uses: Audio → Transcription → CAD-LLM → DXF
    for faster and more cost-effective 2D CAD generation.
    
    Args:
        file: Audio file (mp3, wav, m4a, ogg, flac, webm)
        language: Language code (default: en, use "auto" for auto-detection)
    
    Returns:
        DXF file as binary response
    """
    """
    if not gemini_transcription_service:
        raise HTTPException(
            status_code=503,
            detail="Gemini transcription service is not configured. Please check GEMINI_API_KEY."
        )
    
    if not cadllm_service:
        raise HTTPException(
            status_code=503,
            detail="CADLLM service is not configured. Please set HF_TOKEN and HF_MODEL_NAME or HF_ENDPOINT_URL."
        )
    
    if not cadllm_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="CADLLM service is not properly configured. Please check HF_TOKEN and model settings."
        )
    
    try:
        # Step 1: Transcribe audio
        logger.info("Transcribing audio file with Gemini...")
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        transcribed_text, detected_language, duration = await gemini_transcription_service.transcribe_file(
            file_content=file_content,
            filename=file.filename or "audio",
            language=language
        )
        
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Transcription returned empty text")
        
        logger.info(f"Transcription successful: {len(transcribed_text)} characters")
        
        # Step 2: Generate DXF using CADLLM
        logger.info("Generating DXF using CAD-LLM model...")
        dxf_bytes, error_msg = await cadllm_service.generate_dxf_from_text(
            text=transcribed_text,
            filename=None
        )
        
        if error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"CADLLM generation failed: {error_msg}"
            )
        
        if not dxf_bytes:
            raise HTTPException(
                status_code=500,
                detail="CADLLM generation returned empty result"
            )
        
        # Generate filename from audio file
        audio_name = (file.filename or "audio").rsplit('.', 1)[0]
        safe_name = audio_name.replace(" ", "_").replace("/", "_")
        
        # Return DXF file as binary response
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_cadllm.dxf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CADLLM DXF generation from audio error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DXF generation failed: {str(e)}"
        )

