"""
    Enterprise Region Management Routes — KRAFZEN AI
    Owner: Hammad
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import EnterprisePermission
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.middlewares.permissions import require_permission
from app.schemas.organization_residency import AssignRegionRequest
from app.services.region_registry import RegionRegistryService
from app.services.residency_service import OrganizationResidencyService
from app.services.supabase_service import supabase_service

router = APIRouter(prefix="/enterprise/region", tags=["Enterprise Region"])


def _get_residency_service() -> OrganizationResidencyService:
    client = supabase_service.client or db
    return OrganizationResidencyService(supabase=client)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_current_region(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.RESIDENCY_READ)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: OrganizationResidencyService = Depends(_get_residency_service),
) -> Dict[str, Any]:
    """Retrieve the authoritative active data residency for an organization."""
    return service.get_organization_residency(organization_id=organization_id)


@router.get("/available", status_code=status.HTTP_200_OK)
async def get_available_regions(
    current_user: Dict[str, Any] = Depends(require_auth),
) -> List[Dict[str, Any]]:
    """List all supported cloud regions and their capabilities (safe public metadata)."""
    regions = RegionRegistryService.get_public_regions()
    return [
        {
            "region_code": r["region_code"],
            "display_name": r["display_name"],
            "status": r["status"],
            "capabilities": r["capabilities"],
        }
        for r in regions
    ]


@router.post("/request", status_code=status.HTTP_200_OK)
async def request_region_assignment(
    payload: AssignRegionRequest,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.RESIDENCY_MANAGE)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: OrganizationResidencyService = Depends(_get_residency_service),
) -> Dict[str, Any]:
    """
    Assign an initial region or initiate a controlled migration workflow.
    Requires workspace owner/admin role and Enterprise subscription entitlement.
    """
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    return service.request_region_assignment_or_migration(
        organization_id=organization_id,
        payload=payload,
        current_user_id=user_id,
    )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_region_status(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.RESIDENCY_READ)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: OrganizationResidencyService = Depends(_get_residency_service),
) -> Dict[str, Any]:
    """Inspect health and live connectivity status across database, storage, and worker pools."""
    return service.get_residency_health_and_status(organization_id=organization_id)


@router.get("/audit", status_code=status.HTTP_200_OK)
async def get_region_audit(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.RESIDENCY_READ)),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: OrganizationResidencyService = Depends(_get_residency_service),
) -> List[Dict[str, Any]]:
    """Fetch append-only residency compliance audit logs for the organization."""
    return service.get_residency_audit_trail(organization_id=organization_id, limit=limit)