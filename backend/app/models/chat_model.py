from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # maintained for backward compatibility but ignored if session_id is used for persistence
    history: list[dict[str, Any]] = []
    # When "US_IRC_BASELINE", runs parallel Gemini JSON extraction + IRC baseline screening (see compliance in response).
    jurisdiction: str | None = None
    previous_image_url: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: str | None = None  # ID of the created assistant message (for feedback)
    original_prompt: str
    ollama_response: str
    validated_response: str
    image_url: str
    remaining_minutes: float  # Legacy field
    request_balance: dict[str, Any] | None = None  # New request-based balance
    compliance: dict[str, Any] | None = None  # Present when jurisdiction requests US IRC screening

class DxfRequest(BaseModel):
    image_url: str
    prompt: str | None = None

class DesignFileRequest(BaseModel):
    image_url: str
    file_type: str  # "dxf" | "dwg"
    prompt: str | None = None

class CreateSessionRequest(BaseModel):
    title: str | None = "New Chat"

class UpdateSessionTitleRequest(BaseModel):
    title: str

class MessageFeedbackRequest(BaseModel):
    reaction: str  # 'up' | 'down'
    reason: str | None = None