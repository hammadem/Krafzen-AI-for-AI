"""
Gemini transcription service using Google Gemini 1.5 Flash
"""

import os
import tempfile
import logging
from typing import Optional, Tuple
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiTranscriptionService:
    """Service for audio transcription using Google Gemini 1.5 Flash"""
    
    def __init__(self):
        """Initialize Gemini Transcription service"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use gemini-2.0-flash-001 as 1.5 is unavailable/deprecated for this key
        self.model_name = "gemini-2.0-flash-001"
        self.model = genai.GenerativeModel(self.model_name)
    
    async def transcribe_file(
        self, 
        file_input, # bytes or UploadFile
        filename: str,
        language: Optional[str] = "en"
    ) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe audio file using Gemini API
        
        Args:
            file_input: Audio file content as bytes or UploadFile
            filename: Original filename
            language: Language code (optional)
        
        Returns:
            Tuple of (transcribed_text, detected_language, duration)
            Note: Gemini doesn't always return exact duration/language in metadata, 
            so these might be None or inferred.
        """
        if not settings.GEMINI_API_KEY:
             raise Exception("Gemini API Key not configured")

        # Validate file extension (Gemini supports common audio formats)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        # Create temporary file
        temp_file_path = None
        upload_ref = None
        
        try:
            # Save to temp file
            temp_fd, temp_file_path = tempfile.mkstemp(suffix=f".{file_ext}")
            with os.fdopen(temp_fd, 'wb') as temp_file:
                if isinstance(file_input, bytes):
                    temp_file.write(file_input)
                else:
                    # Assume UploadFile or generic file-like
                    # Reset cursor if possible
                    if hasattr(file_input, 'seek'):
                        await file_input.seek(0)
                        
                    # Stream in chunks
                    while True:
                        chunk = await file_input.read(1024 * 1024) # 1MB chunks
                        if not chunk:
                            break
                        temp_file.write(chunk)
                temp_file.flush()
            
            logger.info(f"Uploading audio file to Gemini...")
            
            # Upload file to Gemini
            upload_ref = genai.upload_file(temp_file_path, mime_type=f"audio/{file_ext if file_ext != 'mp3' else 'mpeg'}")
            
            # Prompt for transcription
            prompt = "Please transcribe this audio file exactly. Output ONLY the transcription text, no other commentary."
            if language and language != "auto":
                prompt += f" The audio is in {language}."
                
            logger.info("Sending audio to Gemini for transcription...")
            response = await self.model.generate_content_async([prompt, upload_ref])
            
            transcribed_text = response.text.strip()
            
            # Gemini doesn't provide structured metadata like Whisper (duration, language confidence)
            # We'll return the text and defaults.
            detected_language = language if language else "unknown"
            duration = None 
            
            logger.info(f"Gemini Transcription successful: {len(transcribed_text)} characters")
            
            return transcribed_text, detected_language, duration
            
        except Exception as e:
            logger.error(f"Gemini Transcription failed: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
            
        finally:
            # Clean up local temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # Clean up remote file in Gemini Storage (good practice)
            if upload_ref:
                try:
                    upload_ref.delete()
                except Exception:
                    pass

    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        return bool(settings.GEMINI_API_KEY)

# Global instance
try:
    gemini_transcription_service = GeminiTranscriptionService() if settings.GEMINI_API_KEY else None
except Exception as e:
    logger.warning(f"Failed to initialize GeminiTranscriptionService: {e}")
    gemini_transcription_service = None
