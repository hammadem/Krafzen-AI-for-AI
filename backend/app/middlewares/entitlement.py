"""
    Enterprise Entitlement Middleware / Dependency
    Enforces server-side Tier checks.
"""

from typing import Any, Dict
from uuid import UUID
from fastapi import Depends, HTTPException, Query, status
from app.utils.logger import logger

from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.services.supabase_service import supabase_service

async def require_enterprise_entitlement(
    organization_id: UUID = Query(..., description="Enterprise workspace/organization UUID"),
    current_user: Dict[str, Any] = Depends(require_auth),
) -> UUID:
    """
    FastAPI dependency that:
    1. Authenticates the requesting user via require_auth.
    2. Verifies the organization exists in workspaces table.
    3. Validates that the requesting user holds an active Enterprise tier.
    4. Returns the validated organization_id to the route handler.
    """
    user_id = str(current_user.get("id") or current_user.get("user_id"))
    client = supabase_service.client or db

    # 1. Verify workspace actually exists
    try:
        ws_res = (
            client.table("workspaces")
            .select("id")
            .eq("id", str(organization_id))
            .execute()
        )
    except Exception as e:
        logger.error(f"Error querying workspaces: {e}")
        ws_res = None

    if not ws_res or not ws_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "ORGANIZATION_NOT_FOUND",
                    "message": f"Organization '{organization_id}' does not exist.",
                }
            },
        )

    # 2. Check user subscription tier
    try:
        sub_res = (
            client.table("user_subscriptions")
            .select("plan_name, plan_tier, subscription_status")
            .eq("user_id", user_id)
            .execute()
        )
        if sub_res and sub_res.data:
            row = sub_res.data[0]
            plan = (row.get("plan_name") or row.get("plan_tier") or "").lower()
            status_val = (row.get("subscription_status") or "").lower()
            
            if plan in ("enterprise", "enterprise_plus") and status_val in ("active", "trial"):
                return organization_id
    except Exception as e:
        logger.error(f"Error querying user_subscriptions: {e}")

    # 3. User does not have active Enterprise entitlement
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": {
                "code": "ENTITLEMENT_DENIED",
                "message": "White-label branding and reporting are exclusive to Enterprise organizations.",
            }
        },
    )