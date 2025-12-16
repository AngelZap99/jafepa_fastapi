import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, text

from src.shared.models import user  # noqa: F401
from src.modules.router import api_router
from src.shared.database.database_config import engine
from src.shared.database.dependencies import SessionDep, get_session  # noqa: F401


# =========================
# Dependencies
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown."""
    # -- STARTUP the app
    db_dialect = os.getenv("DB_DIALECT", "")
    if db_dialect.lower() == "postgresql":
        with engine.begin() as conn:
            # Create pgcrypto extension for gen_random_uuid()
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    # Create all tables
    SQLModel.metadata.create_all(engine)
    try:
        yield
    finally:
        # SHUTDOWN the app
        engine.dispose()


# =========================
# Application
# =========================
app = FastAPI(
    title="Jafepa API",
    description="API for managing jafepa data",
    version="0.0.1",
    lifespan=lifespan,
)


# =========================
# Middlewares
# =========================
# Middleware CORS -- permitir frontend en localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],  # puedes agregar otros si quieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# API routers
# =========================
app.include_router(api_router)
