def test_brand_catalog_endpoints(client, catalog_seed):
    listed = client.get("/api/brands/list")
    assert listed.status_code == 200, listed.text

    created = client.post("/api/brands/create", json={"name": "Brand Test"})
    assert created.status_code == 201, created.text
    brand_id = created.json()["id"]

    got = client.get(f"/api/brands/{brand_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Brand Test"

    updated = client.put(f"/api/brands/update/{brand_id}", json={"name": "Brand Test 2"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Brand Test 2"

    deleted = client.delete(f"/api/brands/delete/{brand_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False


def test_category_catalog_endpoints(client, catalog_seed):
    listed = client.get("/api/categories/list")
    assert listed.status_code == 200, listed.text

    created = client.post(
        "/api/categories/create",
        json={"name": "Category Test", "description": "Root", "parent_id": None},
    )
    assert created.status_code == 201, created.text
    category_id = created.json()["id"]

    got = client.get(f"/api/categories/{category_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Category Test"

    updated = client.put(
        f"/api/categories/update/{category_id}",
        json={"description": "Updated"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == "Updated"

    deleted = client.delete(f"/api/categories/delete/{category_id}")
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


def test_product_catalog_endpoints(client, catalog_seed, db_session):
    from src.shared.models.inventory.inventory_model import Inventory

    category_id = catalog_seed["category_id"]
    brand_id = catalog_seed["brand_id"]
    warehouse_id = catalog_seed["warehouse_id"]

    created = client.post(
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

    listed = client.get("/api/products/list")
    assert listed.status_code == 200, listed.text
    assert any(p["id"] == product_id for p in listed.json())

    got = client.get(f"/api/products/{product_id}")
    assert got.status_code == 200, got.text
    assert got.json()["name"] == "Product Test"

    db_session.add(
        Inventory(
            stock=5,
            box_size=1,
            avg_cost=1.0,
            last_cost=1.0,
            warehouse_id=warehouse_id,
            product_id=product_id,
            is_active=True,
        )
    )
    db_session.commit()

    updated = client.put(
        f"/api/products/update/{product_id}",
        data={"name": "Product Test 2"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Product Test 2"

    stock = client.get(f"/api/products/list-stock?warehouse_id={warehouse_id}")
    assert stock.status_code == 200, stock.text
    assert any(p["id"] == product_id for p in stock.json())

    deleted = client.delete(f"/api/products/delete/{product_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False
