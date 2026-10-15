"""
Pydantic schemas for GPT-4 parsing requests and responses
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CADFileType(str, Enum):
    """Supported CAD file types"""
    DXF = "dxf"
    DWG = "dwg"
    REVIT = "revit"
    STEP = "step"

class ParsingRequest(BaseModel):
    """Request schema for GPT-4 parsing"""
    text: str = Field(..., description="Transcribed text to parse", min_length=1)
    file_type: CADFileType | None = Field(default=CADFileType.DXF, description="Target CAD file type")
    additional_context: str | None = Field(None, description="Additional context for parsing")

class ParsedInstruction(BaseModel):
    """Parsed CAD instruction"""
    command: str = Field(..., description="CAD command/operation")
    parameters: dict[str, Any] = Field(..., description="Command parameters")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

class ParsingResponse(BaseModel):
    """Response schema for parsing"""
    status: str = Field(..., description="Status of parsing")
    instructions: list[ParsedInstruction] = Field(..., description="Parsed CAD instructions")
    file_type: CADFileType = Field(..., description="Target file type")
    raw_gpt_response: str | None = Field(None, description="Raw GPT-4 response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class ParsingError(BaseModel):
    """Error response schema"""
    status: str = "error"
    message: str = Field(..., description="Error message")
    error_code: str | None = None

