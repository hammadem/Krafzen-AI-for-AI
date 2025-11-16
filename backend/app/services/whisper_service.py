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
        
        # Create temporary file with proper extension for OpenAI to detect format
        temp_file_path = None
        try:
            # Use a temporary file with the correct extension
            temp_fd, temp_file_path = tempfile.mkstemp(suffix=f".{file_ext}")
            try:
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    temp_file.write(file_content)
                    temp_file.flush()
                
                # Open file for transcription
                # Read file content and create a BytesIO object for better compatibility
                with open(temp_file_path, "rb") as f:
                    file_bytes = f.read()
                
                # Create a BytesIO object with the file content
                from io import BytesIO
                audio_file = BytesIO(file_bytes)
                audio_file.name = f"audio.{file_ext}"  # Set filename for OpenAI to detect format
                
                # Call Whisper API
                # OpenAI detects format from filename extension in BytesIO.name
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
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        except Exception as e:
            # Re-raise the exception after cleanup
            raise
    
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
        import re
        
        # Convert Google Drive sharing URLs to direct download URLs
        gdrive_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', audio_url)
        if gdrive_match:
            file_id = gdrive_match.group(1)
            audio_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            logger.info(f"Converted Google Drive URL to direct download: {audio_url}")
        
        # Download audio file - follow redirects (needed for Google Drive, etc.)
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            file_content = response.content
        
        # Get filename from Content-Disposition header, URL, or detect from content type
        filename = "audio.mp3"  # Default
        
        # Try to get filename from Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        if content_disposition:
            import re
            match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
            if match:
                filename = match.group(1).strip('"\'')
        
        # If still no filename, try to get from URL
        if filename == "audio.mp3":
            url_path = audio_url.split('?')[0]  # Remove query parameters
            url_filename = os.path.basename(url_path)
            if url_filename and '.' in url_filename:
                filename = url_filename
        
        # If still no extension, try to detect from Content-Type
        if not os.path.splitext(filename)[1]:
            content_type = response.headers.get("Content-Type", "")
            # Map common MIME types to extensions
            mime_to_ext = {
                "audio/mpeg": "mp3",
                "audio/wav": "wav",
                "audio/x-wav": "wav",
                "audio/mp4": "m4a",
                "audio/x-m4a": "m4a",
                "audio/ogg": "ogg",
                "audio/flac": "flac",
                "audio/webm": "webm"
            }
            for mime, ext in mime_to_ext.items():
                if mime in content_type:
                    filename = f"audio.{ext}"
                    break
        
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

