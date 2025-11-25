# src/shared/security/jwt.py

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt  # PyJWT

from shared.config.env_config import env_settings


def _create_token(
    data: Dict[str, Any],
    expires_delta: timedelta,
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode["iat"] = int(now.timestamp())
    to_encode["exp"] = int(expire.timestamp())

    encoded_jwt = jwt.encode(
        to_encode,
        env_settings.JWT_SECRET_KEY,
        algorithm=env_settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_access_token(subject: str) -> str:
    expires = timedelta(minutes=env_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token({"sub": subject, "type": "access"}, expires)


def create_refresh_token(subject: str) -> str:
    expires = timedelta(days=env_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token({"sub": subject, "type": "refresh"}, expires)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Raises exception if token is invalid or expired
    """
    return jwt.decode(
        token,
        env_settings.JWT_SECRET_KEY,
        algorithms=[env_settings.JWT_ALGORITHM],
    )
