import os

os.environ.setdefault("TESTING", "1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.shared.database.dependencies import get_session


@pytest.fixture()
def sqlite_engine():
    import src.shared.models.register_models  # noqa: F401

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client(sqlite_engine, monkeypatch: pytest.MonkeyPatch):
    import main as main_module

    def override_get_session():
        with Session(sqlite_engine) as session:
            yield session

    monkeypatch.setenv("DB_DIALECT", "sqlite")
    monkeypatch.setattr(main_module, "engine", sqlite_engine, raising=True)

    main_module.app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        main_module.app.dependency_overrides.clear()
