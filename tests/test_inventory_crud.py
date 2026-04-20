from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import select

from src.modules.inventory.domain.inventory_service import InventoryService
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import InventoryMovement
from src.shared.models.product.product_model import Product
from src.shared.models.warehouse.warehouse_model import Warehouse
from src.shared.files.local_file_storage import resolve_media_path


PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def _seed_inventory_catalog(
    db_session,
    *,
    stock: int = 5,
    box_size: int = 2,
):
    category = Category(name="Category Inventory", description="Root")
    brand = Brand(name="Brand Inventory")
    warehouse = Warehouse(
        name="Warehouse Inventory",
        address="Inventory address",
        email="inventory@example.com",
        phone="+521111111111",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(brand)
    db_session.refresh(warehouse)

    product = Product(
        name="Product Inventory",
        code="INV-001",
        description="Inventory product",
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    inventory = Inventory(
        stock=stock,
        box_size=box_size,
        avg_cost=Decimal("1.50"),
        last_cost=Decimal("2.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
        is_active=True,
    )
    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)

    return {
        "category": category,
        "brand": brand,
        "warehouse": warehouse,
        "product": product,
        "inventory": inventory,
    }


def test_inventory_list_returns_expanded_relations(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)

    response = auth_client.get("/api/inventory/list")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    item = payload[0]
    assert item["id"] == data["inventory"].id
    assert item["warehouse"]["id"] == data["warehouse"].id
    assert item["warehouse"]["name"] == data["warehouse"].name
    assert item["product"]["id"] == data["product"].id
    assert item["product"]["category"]["id"] == data["category"].id
    assert item["product"]["brand"]["id"] == data["brand"].id


def test_inventory_create_initializes_costs_and_registers_manual_movement(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)
    product = Product(
        name="Second product",
        code="INV-002",
        description="Second inventory product",
        category_id=data["category"].id,
        brand_id=data["brand"].id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": product.id,
            "warehouse_id": data["warehouse"].id,
            "stock": 7,
            "box_size": 3,
            "is_active": True,
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert Decimal(str(payload["avg_cost"])) == Decimal("0.00")
    assert Decimal(str(payload["last_cost"])) == Decimal("0.00")
    assert payload["product"]["id"] == product.id
    assert payload["warehouse"]["id"] == data["warehouse"].id

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.inventory_id == payload["id"])
        ).all()
    )
    assert len(movements) == 1
    movement = movements[0]
    assert movement.source_type == InventorySourceType.MANUAL
    assert movement.event_type == InventoryEventType.MANUAL_CREATED
    assert movement.movement_type == InventoryMovementType.IN_
    assert movement.value_type == InventoryValueType.COST
    assert movement.quantity == 7
    assert movement.prev_stock == 0
    assert movement.new_stock == 7


def test_inventory_create_with_zero_stock_does_not_register_movement(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)
    product = Product(
        name="Third product",
        code="INV-003",
        description="Third inventory product",
        category_id=data["category"].id,
        brand_id=data["brand"].id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": product.id,
            "warehouse_id": data["warehouse"].id,
            "stock": 0,
            "box_size": 1,
            "is_active": True,
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.inventory_id == payload["id"])
        ).all()
    )
    assert movements == []


def test_inventory_datetimes_are_serialized_with_utc_offset_and_filters_accept_naive_datetimes(
    auth_client, db_session
):
    data = _seed_inventory_catalog(db_session)
    product = Product(
        name="UTC product",
        code="INV-UTC-001",
        description="UTC inventory product",
        category_id=data["category"].id,
        brand_id=data["brand"].id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    created = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": product.id,
            "warehouse_id": data["warehouse"].id,
            "stock": 3,
            "box_size": 1,
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["created_at"].endswith("+00:00")
    assert payload["updated_at"].endswith("+00:00")

    movements = auth_client.get("/api/inventory/movements")
    assert movements.status_code == 200, movements.text
    movement = movements.json()[0]
    assert movement["movement_date"].endswith("+00:00")
    assert movement["created_at"].endswith("+00:00")
    assert movement["updated_at"].endswith("+00:00")
    assert "unit_value" in movement
    assert "unit_cost" not in movement

    naive_from = payload["created_at"].split("+")[0]
    aware_to = payload["created_at"]
    filtered = auth_client.get(
        "/api/inventory/movements",
        params={"from_date": naive_from, "to_date": aware_to},
    )
    assert filtered.status_code == 200, filtered.text


def test_inventory_create_returns_404_for_missing_product_or_warehouse(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)

    missing_product = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": 999,
            "warehouse_id": data["warehouse"].id,
            "stock": 1,
            "box_size": 1,
            "is_active": True,
        },
    )
    assert missing_product.status_code == 404, missing_product.text
    assert missing_product.json()["message"] == "Producto no encontrado"

    missing_warehouse = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": data["product"].id,
            "warehouse_id": 999,
            "stock": 1,
            "box_size": 1,
            "is_active": True,
        },
    )
    assert missing_warehouse.status_code == 404, missing_warehouse.text
    assert missing_warehouse.json()["message"] == "Almacén no encontrado"


def test_inventory_create_returns_409_for_duplicate_unique_key(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)

    response = auth_client.post(
        "/api/inventory/create",
        json={
            "product_id": data["product"].id,
            "warehouse_id": data["warehouse"].id,
            "stock": 9,
            "box_size": data["inventory"].box_size,
            "is_active": True,
        },
    )

    assert response.status_code == 409, response.text
    payload = response.json()
    assert (
        payload["message"]
        == "Ya existe un inventario para este producto, almacén y tamaño de caja."
    )
    assert payload["errors"][0]["field"] == "product_id"


def test_inventory_update_only_changes_allowed_fields_and_records_stock_delta(auth_client, db_session):
    data = _seed_inventory_catalog(db_session, stock=10, box_size=4)

    response = auth_client.put(
        f"/api/inventory/update/{data['inventory'].id}",
        json={"stock": 6, "box_size": 5, "is_active": False},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["stock"] == 6
    assert payload["box_size"] == 5
    assert payload["is_active"] is False
    assert Decimal(str(payload["avg_cost"])) == data["inventory"].avg_cost
    assert Decimal(str(payload["last_cost"])) == data["inventory"].last_cost

    movements = (
        db_session.exec(
            select(InventoryMovement).where(
                InventoryMovement.inventory_id == data["inventory"].id
            )
        ).all()
    )
    assert len(movements) == 1
    movement = movements[0]
    assert movement.source_type == InventorySourceType.MANUAL
    assert movement.event_type == InventoryEventType.MANUAL_STOCK_ADJUSTED
    assert movement.movement_type == InventoryMovementType.OUT
    assert movement.quantity == 4
    assert movement.prev_stock == 10
    assert movement.new_stock == 6


def test_inventory_update_rejects_manual_cost_changes(auth_client, db_session):
    data = _seed_inventory_catalog(db_session)

    response = auth_client.put(
        f"/api/inventory/update/{data['inventory'].id}",
        json={"avg_cost": 20},
    )

    assert response.status_code == 422, response.text


def test_inventory_create_with_product_is_transactional_and_returns_expanded_inventory(
    auth_client, db_session
):
    data = _seed_inventory_catalog(db_session)

    response = auth_client.post(
        "/api/inventory/create-with-product",
        data={
            "name": "Created with inventory",
            "code": "INV-CWP-001",
            "description": "Created in one request",
            "category_id": str(data["category"].id),
            "brand_id": str(data["brand"].id),
            "warehouse_id": str(data["warehouse"].id),
            "stock": "3",
            "box_size": "6",
            "is_active": "true",
        },
        files={"image_file": ("product.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["stock"] == 3
    assert Decimal(str(payload["avg_cost"])) == Decimal("0.00")
    assert Decimal(str(payload["last_cost"])) == Decimal("0.00")
    assert payload["warehouse"]["id"] == data["warehouse"].id
    assert payload["product"]["code"] == "INV-CWP-001"
    assert payload["product"]["category"]["id"] == data["category"].id
    assert payload["product"]["brand"]["id"] == data["brand"].id
    assert payload["product"]["image"].startswith("http://testserver/media/product-images/")
    image_path = resolve_media_path(payload["product"]["image"])
    assert image_path is not None and image_path.exists()

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.inventory_id == payload["id"])
        ).all()
    )
    assert len(movements) == 1


def test_inventory_create_with_product_rolls_back_product_on_conflict(
    auth_client, db_session, monkeypatch
):
    data = _seed_inventory_catalog(db_session)

    def raise_conflict(self, **_kwargs):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Inventory already exists for this product, warehouse, and box size",
                "errors": [
                    {
                        "field": "product_id",
                        "message": "Duplicate inventory for selected warehouse and box size",
                    }
                ],
            },
        )

    monkeypatch.setattr(
        InventoryService,
        "_ensure_inventory_unique",
        raise_conflict,
        raising=True,
    )

    response = auth_client.post(
        "/api/inventory/create-with-product",
        data={
            "name": "Should rollback",
            "code": "INV-CWP-ROLLBACK",
            "description": "Rollback product",
            "category_id": str(data["category"].id),
            "brand_id": str(data["brand"].id),
            "warehouse_id": str(data["warehouse"].id),
            "stock": "2",
            "box_size": "1",
            "is_active": "true",
        },
    )

    assert response.status_code == 409, response.text
    product = db_session.exec(
        select(Product).where(Product.code == "INV-CWP-ROLLBACK")
    ).first()
    assert product is None
