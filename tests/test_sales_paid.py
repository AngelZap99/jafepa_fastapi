from datetime import date
from decimal import Decimal

from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
)
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.client.client_model import Client
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import InventoryMovement
from src.shared.models.product.product_model import Product
from src.shared.models.warehouse.warehouse_model import Warehouse


def _seed_inventory_and_client(db_session, *, stock: int = 10) -> tuple[Inventory, Client]:
    category = Category(name="Category")
    brand = Brand(name="Brand")
    warehouse = Warehouse(
        name="Main warehouse",
        address="Some address",
        email="warehouse@example.com",
        phone="+521234567890",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Product",
        code="PROD-001",
        description=None,
        category_id=category.id,
        subcategory_id=None,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()

    inventory = Inventory(
        stock=stock,
        box_size=1,
        avg_cost=1.0,
        last_cost=1.0,
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    client = Client(name="Client", email="client@example.com", phone=None)
    db_session.add(inventory)
    db_session.add(client)
    db_session.commit()

    db_session.refresh(inventory)
    db_session.refresh(client)
    return inventory, client


def test_sale_can_be_marked_paid_and_applies_inventory(client, db_session):
    starting_stock = 10
    quantity = 3
    unit_price = Decimal("2.50")

    inventory, client_obj = _seed_inventory_and_client(db_session, stock=starting_stock)

    created = client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "notes": "test",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inventory.id,
                    "quantity_units": quantity,
                    "price": str(unit_price),
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    paid = client.put(f"/api/sales/update-status/{sale_id}", json={"status": "PAID"})
    assert paid.status_code == 200, paid.text
    paid_sale = paid.json()

    assert paid_sale["status"] == "PAID"
    assert paid_sale["lines"][0]["inventory_applied"] is True

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == starting_stock - quantity

    movements = (
        db_session.query(InventoryMovement)
        .filter(InventoryMovement.sale_line_id == sale_line_id)
        .all()
    )
    assert len(movements) == 1
    movement = movements[0]
    assert movement.source_type == InventorySourceType.SALE
    assert movement.event_type == InventoryEventType.SALE_APPROVED
    assert movement.movement_type == InventoryMovementType.OUT
    assert movement.quantity == quantity
    assert movement.unit_cost == unit_price
    assert movement.prev_stock == starting_stock
    assert movement.new_stock == starting_stock - quantity


def test_marking_sale_paid_twice_is_idempotent(client, db_session):
    starting_stock = 5
    quantity = 2

    inventory, client_obj = _seed_inventory_and_client(db_session, stock=starting_stock)

    created = client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_units": quantity, "price": "1.00"}],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    first = client.put(f"/api/sales/update-status/{sale_id}", json={"status": "PAID"})
    assert first.status_code == 200, first.text

    second = client.put(f"/api/sales/update-status/{sale_id}", json={"status": "PAID"})
    assert second.status_code == 200, second.text

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == starting_stock - quantity

    movements = (
        db_session.query(InventoryMovement)
        .filter(InventoryMovement.sale_line_id == sale_line_id)
        .all()
    )
    assert len(movements) == 1


def test_mark_paid_returns_409_if_stock_would_go_negative(client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=2)

    created = client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_units": 2, "price": "1.00"}],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    # Simulate a concurrent stock change after the sale was drafted.
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    inv.stock = 1
    db_session.add(inv)
    db_session.commit()

    paid = client.put(f"/api/sales/update-status/{sale_id}", json={"status": "PAID"})
    assert paid.status_code == 409, paid.text
    assert paid.json()["detail"] == "Inventory stock cannot be negative"

    sale_after = client.get(f"/api/sales/{sale_id}")
    assert sale_after.status_code == 200, sale_after.text
    assert sale_after.json()["status"] == "DRAFT"

    movements = (
        db_session.query(InventoryMovement)
        .filter(InventoryMovement.sale_line_id == sale_line_id)
        .all()
    )
    assert len(movements) == 0
