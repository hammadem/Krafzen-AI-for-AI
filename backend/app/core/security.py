"""JWT and password security utilities."""
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def decode_supabase_token(token: str):
    import logging
    logger = logging.getLogger(__name__)
    try:
        # PyJWT decode
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_signature": False}
        )
        return payload
    except Exception as e:
        logger.error(f"JWT decode error: {e}", exc_info=True)
        # Hint when signature verification fails: secret must match the Supabase project that issued the token
        if "Signature verification failed" in str(e) or "signature" in str(e).lower():
            try:
                unverified = jwt.decode(token, options={"verify_signature": False})
                iss = unverified.get("iss", "")
                logger.warning(
                    "JWT signature verification failed. Ensure SUPABASE_JWT_SECRET on this service "
                    "matches the JWT Secret of the Supabase project that issued the token (same project "
                    "as the frontend's NEXT_PUBLIC_SUPABASE_URL). Token iss=%s",
                    iss,
                )
            except Exception:
                logger.warning(
                    "JWT signature verification failed. Set SUPABASE_JWT_SECRET on this service "
                    "to the JWT Secret from Supabase Dashboard → Project Settings → API.",
                )
        return None


def create_access_token(data: dict, expires_minutes: int = 30):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,   
        algorithm="HS256"
    )
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)
