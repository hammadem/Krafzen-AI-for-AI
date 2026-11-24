"""Authenticated Supabase user boundary for all paid and private APIs."""
import logging
from typing import Any

from fastapi import Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.core.security import decode_supabase_token


class ErrorResponse(BaseModel):
    error: str


async def require_auth(authorization: str = Header(None)) -> dict[str, Any]:
    """Reject any token whose signing key/claims cannot be verified."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Missing Authorization header").model_dump(),
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid Authorization format").model_dump(),
        )
    token = authorization[7:].strip()
    if not token or any(ch.isspace() for ch in token):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid Authorization format").model_dump(),
        )

    # An asymmetric-key fetch may take network time. Never block the async
    # event loop while validating a public Supabase JWKS signature.
    payload = await run_in_threadpool(decode_supabase_token, token)
    if not payload:
        logging.getLogger(__name__).warning("Rejected unverified user access token")
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid or expired token").model_dump(),
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(error="Invalid user access token").model_dump(),
        )
    # Issuer, authenticated role, expiry and audience were checked inside the
    # same cryptographically verified decode; never re-read untrusted claims.
    return {"user_id": user_id}


async def require_auth_optional(
    authorization: str | None = Header(None),
) -> dict[str, Any] | None:
    if not authorization:
        return None
    try:
        return await require_auth(authorization)
    except HTTPException:
        return None
