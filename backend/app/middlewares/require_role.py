"""
Role-based access control middleware.
TODO: Replace stub role with real DB lookup once workspace roles migration runs.
"""

from typing import Any

from fastapi import Depends, HTTPException

from app.core.permissions import Role
from app.middlewares.auth import require_auth


def require_role(required_role : str):
    """
    Dependency that checks if the current user has the required role.
    Usage: Depends(require_role("admin"))
    """
    async def check_role(user : dict[str, Any] = Depends(require_auth)):
        #TODO fetch role from db once migrations run
        user_role = user.get("role", Role.MEMBER)

        if required_role == Role.ADMIN and user_role != Role.ADMIN:
            raise HTTPException( status_code = 403, detail={"error": "Admin access required"})
        
        if required_role == Role.MEMBER and user_role == Role.VIEWER:
             raise HTTPException(status_code=403,detail={"error": "Member access required"})
        
        return user
    return check_role