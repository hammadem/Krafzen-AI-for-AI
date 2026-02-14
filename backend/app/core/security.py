"""JWT and password security utilities."""
from datetime import datetime, timedelta, timezone
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
            options={"verify_aud": False}
        )
        return payload
    except Exception as e:
        logger.error(f"JWT decode error: {e}", exc_info=True)
        # Debug: try unverified decode to see what's inside
        try:
             unverified = jwt.decode(token, options={"verify_signature": False})
             logger.debug(f"Unverified token payload: {unverified}")
        except:
             pass
        return None


def create_access_token(data: dict, expires_minutes: int = 30):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
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
