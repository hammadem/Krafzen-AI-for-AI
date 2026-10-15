from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ActivityActor(BaseModel):
    user_id: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None


class ActivityEventResponse(BaseModel):
    id: str
    event_name: str
    job_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    actor_user_id: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = {}
    created_at: datetime
    actor: ActivityActor | None = None