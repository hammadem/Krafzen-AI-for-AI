from typing import Any, Dict
from uuid import UUID
from fastapi import Depends, HTTPException, status
from supabase import Client

from app.middlewares.auth import require_auth
from app.services.database_router import RegionalDatabaseRouter
from app.services.supabase_service import supabase_service


async def get_regional_db(
    organization_id: UUID,
    auth: Dict[str, Any] = Depends(require_auth),
) -> Client:
    """
    Enforces server-side resolution of the tenant regional database.
    Validates user membership and prevents client-side routing overrides.
    """
    central_client = supabase_service.client
    if not central_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Central database service is temporarily unavailable.",
                }
            },
        )

    user_id = auth.get("user_id")

    # Verify user belongs to the requested organization
    membership = (
        central_client.table("workspace_members")
        .select("role")
        .eq("workspace_id", str(organization_id))
        .eq("user_id", str(user_id))
        .maybe_single()
        .execute()
    )

    if not membership.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN_ORGANIZATION_ACCESS",
                    "message": "User is not an authorized member of this organization.",
                }
            },
        )

    # Resolve regional database connection
    router = RegionalDatabaseRouter(central_client=central_client)
    return router.resolve_for_organization(organization_id=organization_id)