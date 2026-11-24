"""Authentication only accepts cryptographically verified Supabase sessions."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import decode_supabase_token
from app.middlewares.auth import require_auth


SECRET = "local-ci-supabase-test-secret-with-32-byte-minimum"
ISSUER = "https://trusted-project.supabase.co/auth/v1"


@pytest.fixture(autouse=True)
def signing_config(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://trusted-project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")


def _claims(**kwargs):
    now = datetime.now(UTC)
    return {
        "sub": "user-123", "iss": ISSUER, "aud": "authenticated",
        "role": "authenticated",
        "iat": now, "exp": now + timedelta(minutes=15),
        **kwargs,
    }


def _jwt(secret=SECRET, **claims):
    return jwt.encode(_claims(**claims), secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_accepts_current_signed_supabase_access_token():
    assert await require_auth(f"Bearer {_jwt()}") == {"user_id": "user-123"}


@pytest.mark.asyncio
@pytest.mark.parametrize("claim", [
    {"iss": "https://trusted-project.supabase.co.attacker.test/auth/v1"},
    {"iss": "https://other-project.supabase.co/auth/v1"},
    {"aud": "anon"},
    {"role": "service_role"},
    {"role": "anon"},
    {"sub": ""},
    {"exp": datetime.now(UTC) - timedelta(minutes=5)},
    {"iat": datetime.now(UTC) + timedelta(hours=1)},
])
async def test_rejects_invalid_claims_even_if_signed(claim):
    with pytest.raises(HTTPException) as error:
        await require_auth(f"Bearer {_jwt(**claim)}")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_rejects_unsigned_or_forged_tokens():
    tokens = [
        jwt.encode(_claims(), "attacker-controlled-secret", algorithm="HS256"),
        jwt.encode(_claims(), key=None, algorithm="none"),
        _jwt() + "tamper",
    ]
    for token in tokens:
        with pytest.raises(HTTPException) as error:
            await require_auth(f"Bearer {token}")
        assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_rejects_missing_expiry_and_missing_audience():
    for missing in ("exp", "aud", "iat", "iss"):
        payload = _claims()
        del payload[missing]
        with pytest.raises(HTTPException) as error:
            await require_auth(f"Bearer {jwt.encode(payload, SECRET, algorithm='HS256')}")
        assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_signing_secret_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    with pytest.raises(HTTPException) as error:
        await require_auth(f"Bearer {_jwt()}")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_unsafe_configured_http_issuer_cannot_authorize_users(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "http://trusted-project.supabase.co")
    with pytest.raises(HTTPException) as error:
        await require_auth(f"Bearer {_jwt()}")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_asymmetric_signed_tokens_require_trusted_supabase_jwks(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        _claims(), private, algorithm="RS256", headers={"kid": "ci-pubkey-1"}
    )
    trusted = SimpleNamespace(
        get_signing_key_from_jwt=lambda supplied: SimpleNamespace(key=private.public_key())
    )
    with patch("app.core.security._jwks_client", return_value=trusted) as jwks:
        assert await require_auth(f"Bearer {token}") == {"user_id": "user-123"}
        jwks.assert_called_once_with(ISSUER)


@pytest.mark.asyncio
async def test_asymmetric_token_forged_by_other_key_is_denied(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    attacker = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    legitimate = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        _claims(), attacker, algorithm="RS256", headers={"kid": "wrong"}
    )
    trusted = SimpleNamespace(
        get_signing_key_from_jwt=lambda supplied: SimpleNamespace(key=legitimate.public_key())
    )
    with patch("app.core.security._jwks_client", return_value=trusted):
        with pytest.raises(HTTPException) as error:
            await require_auth(f"Bearer {token}")
    assert error.value.status_code == 401


def test_unsigned_claims_are_never_returned_as_verified_claims():
    forged = jwt.encode(_claims(), "attacker-secret", algorithm="HS256")
    assert decode_supabase_token(forged) is None
