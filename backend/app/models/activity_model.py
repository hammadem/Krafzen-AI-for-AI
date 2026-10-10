from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActivityActor(BaseModel):
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ActivityEventResponse(BaseModel):
    event_id: str
    organization_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    timestamp: datetime

    # Compatibility aliases for existing activity feed clients.
    id: Optional[str] = None
    event_name: Optional[str] = None
    job_id: Optional[str] = None
    project_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    actor: Optional[ActivityActor] = None