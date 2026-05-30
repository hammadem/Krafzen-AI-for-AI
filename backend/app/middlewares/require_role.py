"""
Role-based access control middleware.
TODO: Replace stub role with real DB lookup once workspace roles migration runs.
"""

from fastapi import HTTPException, Depends
from typing import Dict, Any
from app.middlewares.auth import require_auth
from app.core.permissions import Role

def require_role(required_role : str):
    """
    Dependency that checks if the current user has the required role.
    Usage: Depends(require_role("admin"))
    """
    async def check_role(user : Dict[str, Any] = Depends(require_auth)):
        #TODO fetch role from db once migrations run
        user_role = user.get("role", Role.MEMBER)

        if required_role == Role.ADMIN and user_role != Role.ADMIN:
            raise HTTPException( status_code = 403, detail={"error": "Admin access required"})
        
        if required_role == Role.MEMBER and user_role == Role.VIEWER:
             raise HTTPException(status_code=403,detail={"error": "Member access required"})
        
        return user
    return check_role