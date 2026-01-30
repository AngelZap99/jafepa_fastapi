import os

os.environ.setdefault("TESTING", "1")

import sys
from pathlib import Path

# Ensure project root is importable when running `pytest` directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


@pytest.fixture()
def db_session(sqlite_engine):
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture()
def auth_headers(client):
    email = "tester@example.com"
    password = "StrongPass1"

    created = client.post(
        "/api/users/createUser",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    assert created.status_code in {201, 409}, created.text

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def catalog_seed(db_session):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.client.client_model import Client
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = Category(name="Category Seed", description=None, parent_id=None)
    brand = Brand(name="Brand Seed")
    warehouse = Warehouse(
        name="Warehouse Seed",
        address="Seed address",
        email="warehouse.seed@example.com",
        phone="+521111111111",
    )
    client = Client(name="Client Seed", email="client.seed@example.com", phone=None)

    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.add(client)
    db_session.commit()

    db_session.refresh(category)
    db_session.refresh(brand)
    db_session.refresh(warehouse)
    db_session.refresh(client)

    return {
        "category_id": category.id,
        "brand_id": brand.id,
        "warehouse_id": warehouse.id,
        "client_id": client.id,
    }
