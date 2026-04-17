def test_brand_catalog_endpoints(auth_client, catalog_seed):
    listed = auth_client.get("/api/brands/list")
    assert listed.status_code == 200, listed.text

    created = auth_client.post("/api/brands/create", json={"name": "Brand Test"})
    assert created.status_code == 201, created.text
    brand_id = created.json()["id"]

    got = auth_client.get(f"/api/brands/{brand_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Brand Test"

    updated = auth_client.put(f"/api/brands/update/{brand_id}", json={"name": "Brand Test 2"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Brand Test 2"

    deleted = auth_client.delete(f"/api/brands/delete/{brand_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False


def test_category_catalog_endpoints(auth_client, catalog_seed):
    listed = auth_client.get("/api/categories/list")
    assert listed.status_code == 200, listed.text

    created = auth_client.post(
        "/api/categories/create",
        json={"name": "Category Test", "description": "Root"},
    )
    assert created.status_code == 201, created.text
    category_id = created.json()["id"]

    got = auth_client.get(f"/api/categories/{category_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Category Test"

    updated = auth_client.put(
        f"/api/categories/update/{category_id}",
        json={"description": "Updated"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == "Updated"

    deleted = auth_client.delete(f"/api/categories/delete/{category_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False


def test_warehouse_catalog_endpoints_require_auth(client, auth_headers, catalog_seed):
    unauth_list = client.get("/api/warehouses/list")
    assert unauth_list.status_code == 401, unauth_list.text

    listed = client.get("/api/warehouses/list", headers=auth_headers)
    assert listed.status_code == 200, listed.text
    seeded = next(
        (w for w in listed.json() if w["id"] == catalog_seed["warehouse_id"]), None
    )
    assert seeded is not None
    assert seeded["email"] == "warehouse.seed@example.com"
    assert seeded["phone"] == "+521111111111"

    created = client.post(
        "/api/warehouses/create",
        headers=auth_headers,
        json={
            "name": "WH Test",
            "address": "Address 1",
            "email": "warehouse@example.com",
            "phone": "+521234567890",
        },
    )
    assert created.status_code == 201, created.text
    warehouse_id = created.json()["id"]
    assert created.json()["email"] == "warehouse@example.com"
    assert created.json()["phone"] == "+521234567890"

    got = client.get(f"/api/warehouses/{warehouse_id}", headers=auth_headers)
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "WH Test"
    assert got.json()["email"] == "warehouse@example.com"
    assert got.json()["phone"] == "+521234567890"

    updated = client.put(
        f"/api/warehouses/update/{warehouse_id}",
        headers=auth_headers,
        json={"address": "Address 2", "phone": "+521234567891"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["address"] == "Address 2"
    assert updated.json()["phone"] == "+521234567891"

    listed_after = client.get("/api/warehouses/list", headers=auth_headers)
    assert listed_after.status_code == 200, listed_after.text
    created_in_list = next(
        (w for w in listed_after.json() if w["id"] == warehouse_id), None
    )
    assert created_in_list is not None
    assert created_in_list["email"] == "warehouse@example.com"
    assert created_in_list["phone"] == "+521234567891"

    deleted = client.delete(
        f"/api/warehouses/delete/{warehouse_id}", headers=auth_headers
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False


def test_client_catalog_endpoints_require_auth(client, auth_headers):
    unauth_list = client.get("/api/clients/list")
    assert unauth_list.status_code == 401, unauth_list.text

    listed = client.get("/api/clients/list", headers=auth_headers)
    assert listed.status_code == 200, listed.text

    created = client.post(
        "/api/clients/create",
        headers=auth_headers,
        json={
            "name": "Client Test",
            "email": "client.test@example.com",
            "phone": "+521234567890",
        },
    )
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]

    got = client.get(f"/api/clients/{client_id}", headers=auth_headers)
    assert got.status_code == 200, got.text
    assert got.json()["email"] == "client.test@example.com"

    updated = client.put(
        f"/api/clients/update/{client_id}",
        headers=auth_headers,
        json={"phone": "+521234567891"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["phone"] == "+521234567891"

    deleted = client.delete(f"/api/clients/delete/{client_id}", headers=auth_headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False


def test_client_create_allows_optional_email_and_phone(client, auth_headers):
    created = client.post(
        "/api/clients/create",
        headers=auth_headers,
        json={"name": "Cliente Sin Contacto"},
    )
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["name"] == "Cliente Sin Contacto"
    assert data["email"] is None
    assert data["phone"] is None


def test_client_create_normalizes_blank_email_and_phone_to_null(client, auth_headers):
    created = client.post(
        "/api/clients/create",
        headers=auth_headers,
        json={"name": "Cliente Vacío", "email": "", "phone": ""},
    )
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["name"] == "Cliente Vacío"
    assert data["email"] is None
    assert data["phone"] is None


def test_product_catalog_endpoints(auth_client, catalog_seed, db_session):
    from src.shared.models.inventory.inventory_model import Inventory

    category_id = catalog_seed["category_id"]
    brand_id = catalog_seed["brand_id"]
    warehouse_id = catalog_seed["warehouse_id"]

    created = auth_client.post(
        "/api/products/create",
        data={
            "name": "Product Test",
            "code": "sku-1",
            "description": "desc",
            "category_id": str(category_id),
            "brand_id": str(brand_id),
        },
    )
    assert created.status_code == 201, created.text
    product_id = created.json()["id"]
    assert created.json()["code"] == "SKU-1"

    duplicated = auth_client.post(
        "/api/products/create",
        data={
            "name": "Product Test",
            "code": "sku-1",
            "description": "desc",
            "category_id": str(category_id),
            "brand_id": str(brand_id),
        },
    )
    assert duplicated.status_code == 409, duplicated.text
    duplicate_payload = duplicated.json()
    assert (
        duplicate_payload["message"]
        == "Los datos del producto entran en conflicto con registros existentes."
    )
    assert len(duplicate_payload["errors"]) >= 1

    listed = auth_client.get("/api/products/list")
    assert listed.status_code == 200, listed.text
    assert any(p["id"] == product_id for p in listed.json())

    got = auth_client.get(f"/api/products/{product_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Product Test"

    db_session.add(
        Inventory(
            stock=5,
            box_size=1,
            avg_cost=Decimal("1.00"),
            last_cost=Decimal("1.00"),
            warehouse_id=warehouse_id,
            product_id=product_id,
            is_active=True,
        )
    )
    db_session.commit()

    updated = auth_client.put(
        f"/api/products/update/{product_id}",
        data={"name": "Product Test 2"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Product Test 2"

    stock = auth_client.get(f"/api/products/list-stock?warehouse_id={warehouse_id}")
    assert stock.status_code == 200, stock.text
    product_stock = next((p for p in stock.json() if p["id"] == product_id), None)
    assert product_stock is not None
    assert product_stock["stock_total"] == 5
    assert product_stock["stock_boxes_total"] == 5
    assert product_stock["inventory"][0]["available_boxes"] == 5
    assert product_stock["inventory"][0]["sales_last_price"] is None
    assert product_stock["inventory"][0]["sales_avg_price"] is None

    deleted = auth_client.delete(f"/api/products/delete/{product_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False
from decimal import Decimal
