from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, text
from starlette.exceptions import HTTPException as StarletteHTTPException

# Importar modelos y routers
import src.shared.models.register_models  # noqa: F401
from src.modules.router import api_router
from src.shared.database.database_config import engine
from src.shared.database.dependencies import SessionDep, get_session  # noqa: F401
import src.shared.database.session_events  # noqa: F401
from src.shared.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.shared.files.local_file_storage import (
    get_media_root,
    get_media_url_prefixes,
    reset_current_request_base_url,
    set_current_request_base_url,
)


def configure_logging() -> None:
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
    else:
        root_logger.setLevel(log_level)


configure_logging()


# =========================
# Lifespan (startup/shutdown)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown."""
    # -- STARTUP the app
    db_dialect = os.getenv("DB_DIALECT", "")
    if db_dialect.lower() == "postgresql":
        with engine.begin() as conn:
            # Crear extensión pgcrypto para gen_random_uuid()
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)

    try:
        yield
    finally:
        # SHUTDOWN the app
        engine.dispose()


# =========================
# Aplicación FastAPI
# =========================
app = FastAPI(
    title="Jafepa API",
    description="API for managing jafepa data",
    version="0.0.1",
    lifespan=lifespan,
)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
for media_prefix in get_media_url_prefixes():
    app.mount(
        media_prefix,
        StaticFiles(directory=str(get_media_root())),
        name=f"media-{media_prefix.strip('/').replace('/', '-') or 'root'}",
    )


@app.middleware("http")
async def bind_request_base_url(request, call_next):
    token = set_current_request_base_url(str(request.base_url))
    try:
        return await call_next(request)
    finally:
        reset_current_request_base_url(token)


# =========================
# Middleware CORS
# =========================
# Definir origenes permitidos
# Para desarrollo local
allow_origins_raw = os.getenv("ALLOWED_CORS_ORIGINS") or os.getenv("CORS_ORIGINS", "")
allow_origins = [o.strip() for o in allow_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Routers
# =========================
app.include_router(api_router, prefix="/api")


# =========================
# Endpoint de prueba CORS (opcional)
# =========================
from fastapi import Response

@app.get("/test-cors")
def test_cors(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    return {"message": "CORS funcionando"}
