from fastapi import Header, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.security import decode_supabase_token
from app.core.config import settings

class ErrorResponse(BaseModel):
    error: str

async def require_auth(authorization: str = Header(None)) -> Dict[str, Any]:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Missing Authorization header").model_dump()
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid Authorization format").model_dump()
        )

    token = authorization.split(" ")[1]

    payload = decode_supabase_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid or expired token").model_dump()
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Token missing user identifier").model_dump()
        )

    issuer = payload.get("iss", "").rstrip('/')
    
    expected_issuer_url = f"https://{settings.SUPABASE_PROJECT_ID}.supabase.co/auth/v1/"
    expected_issuer = expected_issuer_url.rstrip('/')

    if issuer != expected_issuer:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid token issuer").model_dump()
        )

    return {
        "user_id": user_id
    }

async def require_auth_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Optional authentication variant. Returns user dict if valid, or None if missing/invalid.
    """
    if not authorization:
        return None
    try:
        return await require_auth(authorization)
    except HTTPException:
        return None