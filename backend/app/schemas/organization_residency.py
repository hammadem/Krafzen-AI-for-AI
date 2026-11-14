from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class ResidencyStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    FAILED = "failed"
    SUSPENDED = "suspended"


class AssignRegionRequest(BaseModel):
    region_code: str = Field(..., description="Target region code, e.g. 'us'")
    policy_version: str = Field(default="v1.0", description="Residency compliance policy version")


class OrganizationResidencyResponse(BaseModel):
    organization_id: UUID
    region_code: str
    status: ResidencyStatus
    assigned_at: datetime
    assigned_by: UUID
    last_verified_at: Optional[datetime] = None
    policy_version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True