import os
import re
from fastapi import HTTPException
from sqlmodel import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Environment variables - Default to development
PY_ENV = os.getenv("PY_ENV") or os.getenv("PYENV", "development")
SQL_ECHO = _env_flag("SQL_ECHO", default=False)
IS_TESTING = _env_flag("TESTING") or PY_ENV.lower() == "test"
PRODUCTION_MARKERS = {"prod", "production"}


def _env_tokens(value: str | None) -> set[str]:
    if value is None:
        return set()
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _looks_like_production(value: str | None) -> bool:
    return bool(_env_tokens(value) & PRODUCTION_MARKERS)


def validate_database_target(py_env: str, db_host: str | None, db_name: str | None) -> None:
    if py_env.lower() not in {"development", "dev", "local"}:
        return

    suspicious = []
    if _looks_like_production(db_host):
        suspicious.append(f"DB_HOST={db_host}")
    if _looks_like_production(db_name):
        suspicious.append(f"DB_NAME={db_name}")

    if suspicious:
        raise RuntimeError(
            "Refusing to start in development with a production-like database "
            f"target ({', '.join(suspicious)}). Use a local/dev database or set "
            "PY_ENV=production only in the production runtime."
        )

if IS_TESTING:
    DATABASE_URL = "sqlite+pysqlite:///:memory:"
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
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
        raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

    validate_database_target(PY_ENV, HOST, NAME)

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
        echo=SQL_ECHO,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Number of connections to maintain
        max_overflow=20,  # Max connections beyond pool_size
    )
