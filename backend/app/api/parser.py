"""
GPT-4 Parser API endpoints for converting text to CAD instructions
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from app.services.gpt_parser_service import gpt_parser_service
from app.schemas.parser import (
    ParsingRequest,
    ParsingResponse,
    CADFileType
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/parse", response_model=ParsingResponse)
async def parse_text(
    request: ParsingRequest = Body(...)
):
    """
    Parse transcribed text into CAD instructions using GPT-4
    
    Args:
        request: ParsingRequest with text and file type
    
    Returns:
        ParsingResponse with parsed CAD instructions
    """
    if not gpt_parser_service:
        raise HTTPException(
            status_code=503,
            detail="GPT-4 parser service is not configured. Please check OPENAI_API_KEY."
        )
    
    try:
        # Parse text using GPT-4 service
        instructions, raw_response = await gpt_parser_service.parse_text(
            text=request.text,
            file_type=request.file_type or CADFileType.DXF,
            additional_context=request.additional_context
        )
        
        return ParsingResponse(
            status="success",
            instructions=instructions,
            file_type=request.file_type or CADFileType.DXF,
            raw_gpt_response=raw_response,
            timestamp=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Parsing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )

@router.post("/parse-transcription")
async def parse_transcription(
    transcription_text: str = Body(..., embed=True, description="Transcribed text to parse"),
    file_type: Optional[CADFileType] = Body(CADFileType.DXF, description="Target CAD file type"),
    additional_context: Optional[str] = Body(None, description="Additional context")
):
    """
    Convenience endpoint: Parse transcription text directly
    
    Args:
        transcription_text: Transcribed text
        file_type: Target CAD file type
        additional_context: Optional additional context
    
    Returns:
        ParsingResponse with parsed CAD instructions
    """
    request = ParsingRequest(
        text=transcription_text,
        file_type=file_type,
        additional_context=additional_context
    )
    return await parse_text(request)

