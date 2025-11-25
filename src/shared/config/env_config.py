import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class EnvSettings:
    """Application settings loaded from environment variables."""

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ENCRYPTION_KEY: str = os.getenv("JWT_ENCRYPTION_KEY", "")
    MAX_ACTIVE_SESSIONS: int = int(os.getenv("MAX_ACTIVE_SESSIONS", "2"))

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


__all__ = ["env_settings", "EnvSettings"]
