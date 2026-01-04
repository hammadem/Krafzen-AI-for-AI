"""
Transcriber API endpoints for voice-to-text conversion
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.gemini_transcription_service import gemini_transcription_service
from app.schemas.transcription import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionError
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Query("en", description="Language code (ISO 639-1)")
):
    """
    Transcribe audio file to text using Google Gemini
    
    Args:
        file: Audio file (mp3, wav, m4a, ogg, flac, webm)
        language: Language code (default: en, use "auto" for auto-detection)
    
    Returns:
        TranscriptionResponse with transcribed text
    """
    if not gemini_transcription_service:
        raise HTTPException(
            status_code=503,
            detail="Gemini transcription service is not configured. Please check GEMINI_API_KEY."
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        # Transcribe using Gemini service
        transcribed_text, detected_language, duration = await gemini_transcription_service.transcribe_file(
            file_content=file_content,
            filename=file.filename or "audio",
            language=language
        )
        
        return TranscriptionResponse(
            status="success",
            text=transcribed_text,
            language=detected_language or language or "unknown",
            filename=file.filename,
            duration=duration,
            timestamp=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@router.post("/transcribe-url", response_model=TranscriptionResponse)
async def transcribe_from_url(
    audio_url: str = Query(..., description="URL of the audio file"),
    language: Optional[str] = Query("en", description="Language code (ISO 639-1)")
):
    """
    Transcribe audio from URL
    """
    raise HTTPException(status_code=501, detail="URL transcription is temporarily disabled during migration to Gemini.")
