from fastapi import Header, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.security import decode_supabase_token
from app.core.config import settings
import logging


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

    token = authorization.split(" ")[1].strip()

    payload = decode_supabase_token(token)
    if not payload:
        import logging
        logging.getLogger(__name__).error("Token decode failed or returned None")
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid or expired token").model_dump()
        )



    user_id = payload.get("sub")
    if not user_id:
        logging.getLogger(__name__).error(f"Token missing user ID. Payload keys: {payload.keys()}")
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Token missing user ID").model_dump()
        )
    issuer = payload.get("iss", "").rstrip("/")

    expected_base = f"https://{settings.SUPABASE_PROJECT_ID}.supabase.co"

    # Normalize issuer for check (handle trailing slash mismatch)
    if not issuer.startswith(expected_base):
        logging.getLogger(__name__).error(f"Invalid issuer: {issuer}. Expected startswith: {expected_base}")
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                error=f"Invalid issuer. Expected startswith {expected_base}, got {issuer}"
            ).model_dump()
        )

    # Authentication success
    return {"user_id": user_id}


async def require_auth_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional version.
    Returns:
      - dict(user_id=...) if valid
      - None if missing/invalid
    """

    if not authorization:
        return None

    try:
        return await require_auth(authorization)
    except HTTPException:
        return None
