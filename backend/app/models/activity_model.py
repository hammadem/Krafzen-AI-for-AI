from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class ActivityActor(BaseModel):
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ActivityEventResponse(BaseModel):
    id: str
    event_name: str
    job_id: Optional[str] = None
    project_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    actor: Optional[ActivityActor] = None