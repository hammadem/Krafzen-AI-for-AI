"""
Pydantic schemas for transcription requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TranscriptionRequest(BaseModel):
    """Request schema for transcription"""
    language: Optional[str] = Field(default="en", description="Language code (ISO 639-1)")
    
class TranscriptionResponse(BaseModel):
    """Response schema for transcription"""
    status: str = Field(..., description="Status of transcription")
    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected or specified language")
    filename: Optional[str] = Field(None, description="Original filename")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class TranscriptionError(BaseModel):
    """Error response schema"""
    status: str = "error"
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = None

