from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActivityActor(BaseModel):
    user_id: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None


class ActivityEventResponse(BaseModel):
    event_id: str
    organization_id: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    timestamp: datetime

    # Compatibility aliases for existing activity feed clients.
    id: str | None = None
    event_name: str | None = None
    job_id: str | None = None
    project_id: str | None = None
    actor_user_id: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    actor: ActivityActor | None = None