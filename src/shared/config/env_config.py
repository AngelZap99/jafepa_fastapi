# src/shared/config/env_config.py

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


class EnvSettings:
    """Application settings loaded from environment variables."""

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int_env(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 8 * 60
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS_LEGACY: int = _get_int_env(
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS", 1
    )
    JWT_REFRESH_TOKEN_EXPIRE_HOURS: int = _get_int_env(
        "JWT_REFRESH_TOKEN_EXPIRE_HOURS",
        JWT_REFRESH_TOKEN_EXPIRE_DAYS_LEGACY * 24,
    )
    JWT_ENCRYPTION_KEY: str = os.getenv("JWT_ENCRYPTION_KEY", "")

    @classmethod
    def get_encryption_key(cls) -> Optional[bytes]:
        """Get encryption key as bytes, padded/truncated to 32 bytes for Fernet."""
        if not cls.JWT_ENCRYPTION_KEY:
            return None
        key = cls.JWT_ENCRYPTION_KEY.encode()
        # Pad or truncate to 32 bytes
        if len(key) < 32:
            key = key.ljust(32, b'0')
        elif len(key) > 32:
            key = key[:32]
        return key


env_settings = EnvSettings()
