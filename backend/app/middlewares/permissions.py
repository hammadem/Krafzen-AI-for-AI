"""
    app/middlewares/permissions.py
    Tenant isolation & RBAC authorization dependency with TTL caching for fast response times.
"""
import time
from uuid import UUID
from typing import Dict, Any, Callable, Tuple
from fastapi import HTTPException, status, Depends, Query
from app.middlewares.auth import require_auth
from app.db.supabase_client import db
from app.services.supabase_service import supabase_service
from app.core.permissions import EnterprisePermission, ROLE_PERMISSIONS

# In-memory TTL cache: {(org_id, user_id): (user_role, expires_at_timestamp)}
_PERM_CACHE: Dict[Tuple[str, str], Tuple[str, float]] = {}
_CACHE_TTL_SECONDS = 60.0


def require_permission(required_perm: EnterprisePermission) -> Callable:
    """
    Factory dependency verifying:
    1. Authentication (valid session/JWT).
    2. Tenant Verification & Enterprise Entitlement.
    3. Tenant Boundary Isolation (Prevent cross-org access).
    4. RBAC: User has the specified role permission.
    """
    async def _permission_guard(
        organization_id: UUID = Query(..., description="Target workspace UUID"),
        current_user: Dict[str, Any] = Depends(require_auth),
    ) -> UUID:
        user_id = str(current_user.get("id") or current_user.get("user_id"))
        org_str = str(organization_id)
        cache_key = (org_str, user_id)
        now = time.monotonic()

        # Fast path: use cached tenant & role verification if within 60s TTL
        cached = _PERM_CACHE.get(cache_key)
        if cached and cached[1] > now:
            user_role = cached[0]
        else:
            client = supabase_service.client or db

            # 1. Tenant Verification
            ws_res = (
                client.table("workspaces")
                .select("id, owner_id")
                .eq("id", org_str)
                .execute()
            )
            if not ws_res.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": {
                            "code": "ORGANIZATION_NOT_FOUND",
                            "message": f"Organization '{organization_id}' not found.",
                        }
                    },
                )

            # 2. Verify Enterprise Subscription
            sub_res = (
                client.table("user_subscriptions")
                .select("plan_name, plan_tier, subscription_status")
                .eq("user_id", user_id)
                .execute()
            )
            is_enterprise = False
            if sub_res and sub_res.data:
                row = sub_res.data[0]
                plan = (row.get("plan_name") or row.get("plan_tier") or "").lower()
                status_val = (row.get("subscription_status") or "").lower()
                if plan in ("enterprise", "enterprise_plus") and status_val in ("active", "trial"):
                    is_enterprise = True

            if not is_enterprise:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "ENTITLEMENT_DENIED",
                            "message": "Enterprise subscription required.",
                        }
                    },
                )

            # 3. Cross-Organization Isolation & Membership Resolution
            user_role = None
            member_res = (
                client.table("workspace_members")
                .select("role")
                .eq("workspace_id", org_str)
                .eq("user_id", user_id)
                .execute()
            )

            if member_res.data and len(member_res.data) > 0:
                raw_role = member_res.data[0].get("role")
                user_role = str(raw_role).lower().strip() if raw_role else "member"
            else:
                ws_owner = ws_res.data[0].get("owner_id")
                if ws_owner and str(ws_owner) == user_id:
                    user_role = "admin"

            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "ACCESS_DENIED_CROSS_TENANT",
                            "message": "User is not authorized for this workspace.",
                        }
                    },
                )

            _PERM_CACHE[cache_key] = (user_role, now + _CACHE_TTL_SECONDS)

        # 4. Enforce Role Permissions
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, set())
        if required_perm not in allowed_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": f"Role '{user_role}' lacks required permission: '{required_perm.value}'.",
                    }
                },
            )

        return organization_id

    return _permission_guard