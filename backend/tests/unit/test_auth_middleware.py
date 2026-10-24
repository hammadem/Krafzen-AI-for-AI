import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.middlewares.auth import require_auth


@pytest.mark.asyncio
async def test_require_auth_accepts_configured_supabase_issuer(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "http://127.0.0.1:54321")
    token = jwt.encode(
        {"sub": "user-123", "iss": "http://127.0.0.1:54321/auth/v1"},
        "test-secret",
        algorithm="HS256",
    )

    assert await require_auth(f"Bearer {token}") == {"user_id": "user-123"}


@pytest.mark.asyncio
async def test_require_auth_rejects_wrong_issuer(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://expected.supabase.co")
    token = jwt.encode(
        {"sub": "user-123", "iss": "https://other.supabase.co/auth/v1"},
        "test-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as error:
        await require_auth(f"Bearer {token}")

    assert error.value.status_code == 401
