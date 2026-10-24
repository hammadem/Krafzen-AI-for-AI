"""
Transcriber API endpoints for voice-to-text conversion
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.middlewares.auth import require_auth
from app.schemas.transcription import (
    TranscriptionResponse,
)
from app.services.gemini_transcription_service import gemini_transcription_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse, dependencies=[Depends(require_auth)])
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query("en", description="Language code (ISO 639-1)")
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
        # Transcribe using Gemini service (streaming)
        transcribed_text, detected_language, duration = await gemini_transcription_service.transcribe_file(
            file_input=file,
            filename=file.filename or "audio",
            language=language
        )
        
        return TranscriptionResponse(
            status="success",
            text=transcribed_text,
            language=detected_language or language or "unknown",
            filename=file.filename,
            duration=duration,
            timestamp=datetime.now(UTC)
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid input provided.")
    except Exception:
        logger.exception("Transcription error")
        raise HTTPException(
            status_code=500,
            detail="Transcription failed due to an internal error."
        )

@router.post("/transcribe-url", response_model=TranscriptionResponse, dependencies=[Depends(require_auth)])
async def transcribe_from_url(
    audio_url: str = Query(..., description="URL of the audio file"),
    language: str | None = Query("en", description="Language code (ISO 639-1)")
):
    """
    Transcribe audio from URL
    """
    raise HTTPException(status_code=501, detail="URL transcription is temporarily disabled during migration to Gemini.")
