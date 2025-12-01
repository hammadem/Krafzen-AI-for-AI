"""
DXF Generator API endpoints for converting CAD instructions to DXF files
"""

from fastapi import APIRouter, HTTPException, Body, Response
from typing import Optional, List
from app.schemas.parser import (
    ParsingRequest,
    ParsingResponse,
    ParsedInstruction,
    CADFileType
)
from datetime import datetime
import logging

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


@router.post("/generate-from-text")
async def generate_dxf_from_text(
    request: ParsingRequest = Body(...)
):
    """
    Parse text and generate DXF file in one step
    
    Args:
        request: ParsingRequest with text and file type
    
    Returns:
        DXF file as binary response
    """
    if not gpt_parser_service:
        raise HTTPException(
            status_code=503,
            detail="GPT-4 parser service is not configured. Please check OPENAI_API_KEY."
        )
    
    if not dxf_generator_service:
        raise HTTPException(
            status_code=503,
            detail="DXF generator service is not available. Please check ezdxf installation."
        )
    
    try:
        # Parse text using GPT-4 service
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

