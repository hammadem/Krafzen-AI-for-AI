"""Supabase access-token verification and password security utilities.

User-controlled JWT claims must never authorize paid plans or private project
files until verified against the configured Supabase issuer and signing key.
"""
import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from urllib.parse import urlsplit

import httpx
import jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ASYMMETRIC_ALGORITHMS = frozenset({"RS256", "ES256", "EdDSA"})
_TOKEN_AUDIENCE = "authenticated"
_REQUIRED_CLAIMS = ["exp", "iat", "iss", "sub", "aud"]


def _trusted_issuer() -> str | None:
    """Only operator-configured Supabase hosts may be used as JWT issuers/JWKS."""
    raw = str(settings.SUPABASE_URL or "").rstrip("/")
    try:
        parsed = urlsplit(raw)
        if (not parsed.hostname or not parsed.netloc or parsed.username
                or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            return None
        local = (parsed.hostname in {"127.0.0.1", "localhost"}
                 and (settings.ENVIRONMENT or "").lower() in {"development", "test"})
        if parsed.scheme != "https" and not (local and parsed.scheme == "http"):
            return None
    except (ValueError, TypeError):
        return None
    return raw + "/auth/v1"


@lru_cache(maxsize=8)
def _jwks_client(issuer: str) -> jwt.PyJWKClient:
    # The URL originates exclusively from _trusted_issuer(), never token claims.
    # Cache the JWKS for 5 minutes; support timely signing-key revocation.
    return jwt.PyJWKClient(
        issuer + "/.well-known/jwks.json",
        cache_jwk_set=True,
        lifespan=300,
        timeout=5,
    )



def _verify_hs256_with_auth_server(token: str, issuer: str):
    """Ask the original Supabase Auth service to validate legacy user tokens.

    Supabase recommends this method over distributing shared JWT secrets.
    The returned identity comes from the Auth server's verified response,
    *not* from untrusted token claims or headers. No redirects allowed.
    """
    public_key = str(settings.SUPABASE_ANON_KEY or "").strip()
    if not public_key:
        return None
    try:
        response = httpx.get(
            issuer + "/user",
            headers={
                "apikey": public_key,
                "Authorization": "Bearer " + token,
                "Accept": "application/json",
            },
            timeout=5.0,
            follow_redirects=False,
        )
        if response.status_code != 200:
            return None
        user = response.json()
        if not isinstance(user, dict):
            return None
        uid = user.get("id")
        if not isinstance(uid, str) or not uid.strip():
            return None
        if user.get("aud", "authenticated") != "authenticated":
            return None
        if user.get("role", "authenticated") != "authenticated":
            return None
        return {
            "sub": uid,
            "role": "authenticated",
            "aud": "authenticated",
            "iss": issuer,
            "verified_by": "supabase_auth_server",
        }
    except (httpx.HTTPError, ValueError, TypeError):
        logger.warning("Supabase Auth server unavailable for JWT verification")
        return None


def decode_supabase_token(token: str):
    """Return only verified Supabase authenticated-user claims, or None.

    Legacy HS256 is verified either with the operator's signing secret or
    directly by the trusted Supabase Auth server; asymmetric signing keys
    are discovered from the configured project's public JWKS. Never
    allow 'none' or algorithm confusion, an unsigned decode, missing expiry,
    wrong issuer/audience, or a service-role token.
    """
    issuer = _trusted_issuer()
    if not issuer or not isinstance(token, str) or not 1 <= len(token) <= 8192:
        return None
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm == "HS256":
            signing_key = settings.SUPABASE_JWT_SECRET
            if not signing_key:
                # Verification still occurs at Supabase Auth. Never accept
                # unsigned claims as a workaround for missing legacy secret.
                return _verify_hs256_with_auth_server(token, issuer)
        elif algorithm in _ASYMMETRIC_ALGORITHMS:
            signing_key = _jwks_client(issuer).get_signing_key_from_jwt(token).key
        else:
            return None

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=[algorithm],
            audience=_TOKEN_AUDIENCE,
            issuer=issuer,
            leeway=30,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
                "require": _REQUIRED_CLAIMS,
            },
        )
        if (not isinstance(claims, dict) or claims.get("role") != "authenticated"
                or not isinstance(claims.get("sub"), str)
                or not claims["sub"].strip()):
            return None
        return claims
    except (jwt.PyJWTError, jwt.PyJWKClientError, TypeError, ValueError, OSError):
        # No token contents, secret, unverified issuer or provider exception in logs.
        logger.warning("Supabase access token verification failed")
        return None


def create_access_token(data: dict, expires_minutes: int = 30):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)
