import os
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from app.core.config import settings


class RegionStatus(str, Enum):
    ACTIVE = "active"
    PROVISIONING = "provisioning"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class RegionEntry(BaseModel):
    region_code: str = Field(..., description="Stable identifier, e.g. us")
    display_name: str = Field(..., description="Human-readable region name")
    status: RegionStatus = Field(..., description="Active, provisioning, unavailable or disabled")
    database_config: Dict[str, Any] = Field(..., description="Secure reference to regional database configuration")
    storage_config: Dict[str, Any] = Field(..., description="Secure reference to regional object storage")
    queue_config: Dict[str, Any] = Field(..., description="Regional job queue")
    processing_config: Dict[str, Any] = Field(..., description="Regional worker configuration")
    backup_policy: Dict[str, Any] = Field(..., description="Approved regional recovery policy")
    capabilities: List[str] = Field(default_factory=list, description="Supported regional features")


# Centralized registry definition with 'us' as initial supported region
CENTRAL_REGION_REGISTRY: Dict[str, RegionEntry] = {
    "us": RegionEntry(
        region_code="us",
        display_name="United States",
        status=RegionStatus.ACTIVE,
        database_config={
            "secret_env_ref": "SUPABASE_DATABASE_URL_US",
            "configured": bool(settings.SUPABASE_DATABASE_URL_US),
            "provider": "supabase_postgres",
            "region": "us-east-1",
        },
        storage_config={
            "bucket_name": settings.SUPABASE_STORAGE_BUCKET_US,
            "secret_env_ref": "SUPABASE_STORAGE_KEY_US",
            "configured": bool(settings.SUPABASE_STORAGE_KEY_US),
            "provider": "supabase_s3",
            "region": settings.SUPABASE_STORAGE_REGION_US,
        },
        queue_config={
            "queue_name": settings.US_QUEUE_NAME,
            "provider": "postgres_queue",
        },
        processing_config={
            "worker_pool": settings.US_WORKER_POOL,
            "allowed_binaries": ["ODAFileConverter", "potrace"],
        },
        backup_policy={
            "schedule": "0 2 * * *",  # Daily 02:00 UTC
            "retention_days": 30,
            "cross_region_replication": False,  # Sovereign data must remain in US
        },
        capabilities=[
            "sovereign_storage", 
            "isolated_cad_processing", 
            "white_label_reports"
        ]
    )
}

class RegionRegistryService:
    @staticmethod
    def get_public_regions() -> List[Dict[str, Any]]:
        """
        Returns region catalog sanitized for the frontend.
        Internal credentials, database URLs, and storage secrets are strictly stripped out.
        """
        return [
            {
                "region_code": r.region_code,
                "display_name": r.display_name,
                "status": r.status.value,
                "capabilities": r.capabilities,
                "is_available": r.status == RegionStatus.ACTIVE
            }
            for r in CENTRAL_REGION_REGISTRY.values()
        ]
    
    @staticmethod
    def get_region(region_code: str) -> Optional[RegionEntry]:
        """
        Safe non-throwing reader for internal service health checks and lookups.
        """
        return CENTRAL_REGION_REGISTRY.get(region_code)
    
    @staticmethod
    def validate_region_for_assignment(region_code: str) -> RegionEntry:
        """
        Rejects unsupported regions and verifies infrastructure readiness before assignment.
        """
        # 1. Reject unsupported regions
        if region_code not in CENTRAL_REGION_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "UNSUPPORTED_REGION",
                        "message": f"Region '{region_code}' is not supported by Krafzen."
                    }
                }
            )

        region = CENTRAL_REGION_REGISTRY[region_code]

        # 2. Check region administrative status
        if region.status != RegionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "REGION_NOT_ACTIVE",
                        "message": f"Region '{region_code}' is currently {region.status.value}."
                    }
                }
            )

        # 3. Required infrastructure check (matching secret_env_ref keys)
        db_secret_key = region.database_config.get("secret_env_ref")
        if db_secret_key and not os.getenv(db_secret_key):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "INFRASTRUCTURE_CHECK_FAILED",
                        "message": f"Region '{region_code}' failed infrastructure validation: Database credentials missing."
                    }
                }
            )

        storage_secret_key = region.storage_config.get("secret_env_ref")
        if storage_secret_key and not os.getenv(storage_secret_key):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "INFRASTRUCTURE_CHECK_FAILED",
                        "message": f"Region '{region_code}' failed infrastructure validation: Storage credentials missing."
                    }
                }
            )

        return region