from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, text

# Importar modelos y routers
import src.shared.models.register_models  # noqa: F401
from src.modules.router import api_router
from src.shared.database.database_config import engine
from src.shared.database.dependencies import SessionDep, get_session  # noqa: F401
import src.shared.database.session_events  # noqa: F401


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


# =========================
# Middleware CORS
# =========================
# Definir origenes permitidos
# Para desarrollo local
allow_origins = ["https://jafepa.com","https://www.jafepa.com"]

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
