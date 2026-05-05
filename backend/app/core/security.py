from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(payload: dict, expires_delta: timedelta, token_type: str) -> str:
    data = payload.copy()
    now = datetime.now(timezone.utc)
    data.update({"exp": now + expires_delta, "iat": now, "type": token_type})
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(payload: dict) -> str:
    return _create_token(
        payload=payload,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(payload: dict) -> str:
    return _create_token(
        payload=payload,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

