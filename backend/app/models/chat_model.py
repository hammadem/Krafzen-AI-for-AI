from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    # maintained for backward compatibility but ignored if session_id is used for persistence
    history: List[Dict[str, Any]] = []
    # When "US_IRC_BASELINE", runs parallel Gemini JSON extraction + IRC baseline screening (see compliance in response).
    jurisdiction: Optional[str] = None
    previous_image_url: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: Optional[str] = None  # ID of the created assistant message (for feedback)
    original_prompt: str
    ollama_response: str
    validated_response: str
    image_url: str
    remaining_minutes: float  # Legacy field
    request_balance: Optional[Dict[str, Any]] = None  # New request-based balance
    compliance: Optional[Dict[str, Any]] = None  # Present when jurisdiction requests US IRC screening

class DxfRequest(BaseModel):
    image_url: str
    prompt: Optional[str] = None

class DesignFileRequest(BaseModel):
    image_url: str
    file_type: str  # "dxf" | "dwg"
    prompt: Optional[str] = None

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"

class UpdateSessionTitleRequest(BaseModel):
    title: str

class MessageFeedbackRequest(BaseModel):
    reaction: str  # 'up' | 'down'
    reason: Optional[str] = None