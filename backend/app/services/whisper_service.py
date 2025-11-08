"""
Whisper transcription service using OpenAI Whisper API
"""

import os
import tempfile
from typing import Optional, Tuple
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class WhisperService:
    """Service for audio transcription using OpenAI Whisper"""
    
    def __init__(self):
        """Initialize Whisper service"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "whisper-1"
    
    async def transcribe_file(
        self, 
        file_content: bytes, 
        filename: str,
        language: Optional[str] = "en"
    ) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe audio file using Whisper API
        
        Args:
            file_content: Audio file content as bytes
            filename: Original filename
            language: Language code (optional, auto-detect if None)
        
        Returns:
            Tuple of (transcribed_text, detected_language, duration)
        
        Raises:
            ValueError: If file format is not supported
            Exception: If transcription fails
        """
        # Validate file extension
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if file_ext not in settings.ALLOWED_AUDIO_FORMATS_LIST:
            raise ValueError(f"Unsupported file format: {file_ext}. Allowed: {settings.ALLOWED_AUDIO_FORMATS_LIST}")
        
        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({file_size_mb:.2f}MB) exceeds maximum ({settings.MAX_FILE_SIZE_MB}MB)")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            try:
                temp_file.write(file_content)
                temp_file.flush()
                temp_file_path = temp_file.name
                
                # Open file for transcription
                with open(temp_file_path, "rb") as audio_file:
                    # Call Whisper API
                    transcript = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language if language and language != "auto" else None,
                        response_format="verbose_json"
                    )
                
                # Extract results
                transcribed_text = transcript.text
                detected_language = getattr(transcript, 'language', language)
                duration = getattr(transcript, 'duration', None)
                
                logger.info(f"Transcription successful: {len(transcribed_text)} characters, language: {detected_language}")
                
                return transcribed_text, detected_language, duration
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    
    async def transcribe_from_url(
        self,
        audio_url: str,
        language: Optional[str] = "en"
    ) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe audio from URL using Whisper API
        
        Args:
            audio_url: URL of the audio file
            language: Language code (optional, auto-detect if None)
        
        Returns:
            Tuple of (transcribed_text, detected_language, duration)
        
        Raises:
            Exception: If transcription fails
        """
        import httpx
        
        # Download audio file
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            file_content = response.content
        
        # Get filename from URL or use default
        filename = os.path.basename(audio_url) or "audio.mp3"
        
        # Transcribe using file transcription
        return await self.transcribe_file(file_content, filename, language)
    
    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        return bool(settings.OPENAI_API_KEY)

# Global instance - only create if API key is configured
try:
    whisper_service = WhisperService() if settings.OPENAI_API_KEY else None
except ValueError:
    whisper_service = None

