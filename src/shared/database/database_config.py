import os
from fastapi import HTTPException
from sqlmodel import create_engine
from sqlalchemy.engine import URL

# Environment variables - Default to development
PY_ENV = os.getenv("PYENV", "development")

# DB variables with validation
DIALECT = os.getenv("DB_DIALECT")
DIALECT_DRIVER = os.getenv("DB_DIALECT_DRIVER")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
NAME = os.getenv("DB_NAME")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

# Validate required environment variables
required_vars = {
    "DB_DIALECT": DIALECT,
    "DB_DIALECT_DRIVER": DIALECT_DRIVER,
    "DB_HOST": HOST,
    "DB_PORT": PORT,
    "DB_NAME": NAME,
    "DB_USER": USER,
    "DB_PASSWORD": PASSWORD,
}

missing_vars = [key for key, value in required_vars.items() if value is None]
if missing_vars:
    raise HTTPException(
        status_code=500,
        detail=f"Missing environment variables: {', '.join(missing_vars)}",
    )

# Build database URL (hides password in repr)
DATABASE_URL = URL.create(
    drivername=f"{DIALECT}+{DIALECT_DRIVER}",
    username=USER,
    password=PASSWORD,
    host=HOST,
    port=int(PORT),
    database=NAME,
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=PY_ENV == "development",
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Max connections beyond pool_size
)


__all__ = ["engine"]
