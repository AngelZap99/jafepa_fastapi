from datetime import date
from decimal import Decimal

from sqlmodel import select

from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
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
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()

    inventory = Inventory(
        stock=stock,
        box_size=1,
        avg_cost=Decimal("1.00"),
        last_cost=Decimal("1.00"),
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


def test_sale_can_be_marked_paid_and_applies_inventory(auth_client, db_session):
    starting_stock = 10
    quantity = 3
    unit_price = Decimal("2.50")

    inventory, client_obj = _seed_inventory_and_client(db_session, stock=starting_stock)

    created = auth_client.post(
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

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    paid_sale = paid.json()

    assert paid_sale["status"] == "PAID"
    assert paid_sale["lines"][0]["inventory_applied"] is True

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == starting_stock - quantity
    assert inv.reserved_stock == 0

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.sale_line_id == sale_line_id)
        ).all()
    )
    assert len(movements) == 3
    assert [movement.event_type for movement in movements] == [
        InventoryEventType.SALE_RESERVED,
        InventoryEventType.SALE_RELEASED,
        InventoryEventType.SALE_APPROVED,
    ]
    assert movements[-1].source_type == InventorySourceType.SALE
    assert movements[-1].movement_type == InventoryMovementType.OUT
    assert movements[-1].value_type == InventoryValueType.PRICE
    assert movements[-1].quantity == quantity
    assert movements[-1].unit_value == unit_price
    assert movements[-1].prev_stock == starting_stock
    assert movements[-1].new_stock == starting_stock - quantity


def test_marking_sale_paid_twice_is_idempotent(auth_client, db_session):
    starting_stock = 5
    quantity = 2

    inventory, client_obj = _seed_inventory_and_client(db_session, stock=starting_stock)

    created = auth_client.post(
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

    first = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert first.status_code == 200, first.text

    second = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert second.status_code == 200, second.text

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == starting_stock - quantity
    assert inv.reserved_stock == 0

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.sale_line_id == sale_line_id)
        ).all()
    )
    assert len(movements) == 3


def test_mark_paid_returns_409_if_stock_would_go_negative(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=2)

    created = auth_client.post(
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

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 409, paid.text
    assert paid.json()["message"] == "El inventario no puede quedar en negativo"

    sale_after = auth_client.get(f"/api/sales/{sale_id}")
    assert sale_after.status_code == 200, sale_after.text
    assert sale_after.json()["status"] == "DRAFT"

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.sale_line_id == sale_line_id)
        ).all()
    )
    assert len(movements) == 1
    assert movements[0].event_type == InventoryEventType.SALE_RESERVED


def test_create_sale_rejects_inactive_inventory(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=4)
    inventory.is_active = False
    db_session.add(inventory)
    db_session.commit()

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_units": 1, "price": "1.00"}],
        },
    )

    assert created.status_code == 409, created.text
    assert created.json()["message"] == "El inventario inactivo no puede usarse en ventas"


def test_mark_paid_returns_409_if_inventory_is_inactive(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=4)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_units": 1, "price": "1.00"}],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    inventory.is_active = False
    db_session.add(inventory)
    db_session.commit()

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 409, paid.text
    assert paid.json()["message"] == "El inventario inactivo no puede usarse en ventas"

    sale_after = auth_client.get(f"/api/sales/{sale_id}")
    assert sale_after.status_code == 200, sale_after.text
    assert sale_after.json()["status"] == "DRAFT"

    movements = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.sale_line_id == sale_line_id)
        ).all()
    )
    assert len(movements) == 1
    assert movements[0].event_type == InventoryEventType.SALE_RESERVED


def test_paid_sale_line_can_be_updated_in_place(auth_client, db_session):
    starting_stock = 120
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=starting_stock)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inventory.id,
                    "quantity_boxes": 2,
                    "price": "100.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text

    updated = auth_client.put(
        f"/api/sales/{sale_id}/lines/{sale_line_id}",
        json={
            "quantity_boxes": 3,
            "price": "90.00",
            "price_type": "BOX",
        },
    )
    assert updated.status_code == 200, updated.text
    updated_line = updated.json()
    assert updated_line["quantity_boxes"] == 3
    assert updated_line["price_type"] == "BOX"
    assert Decimal(str(updated_line["box_price"])) == Decimal("90.00")

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == starting_stock - (3 * inventory.box_size)

    movements = (
        db_session.exec(
            select(InventoryMovement)
            .where(InventoryMovement.sale_line_id == sale_line_id)
            .order_by(InventoryMovement.id)
        ).all()
    )
    assert len(movements) == 5
    assert movements[-1].quantity == 3 * inventory.box_size
    assert movements[-1].value_type == InventoryValueType.PRICE
    assert movements[-1].unit_value == Decimal("90.00")


def test_paid_sale_accepts_add_and_delete_line(auth_client, db_session):
    inv1, client_obj = _seed_inventory_and_client(db_session, stock=120)

    # Seed a second inventory for the same client/warehouse flow.
    category_obj = db_session.exec(select(Category)).first()
    brand_obj = db_session.exec(select(Brand)).first()
    warehouse_obj = db_session.exec(select(Warehouse)).first()
    product = Product(
        name="Product 2",
        code="PROD-002",
        description=None,
        category_id=category_obj.id,
        brand_id=brand_obj.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    inv2 = Inventory(
        stock=60,
        box_size=12,
        avg_cost=Decimal("1.00"),
        last_cost=Decimal("1.00"),
        warehouse_id=warehouse_obj.id,
        product_id=product.id,
    )
    db_session.add(inv2)
    db_session.commit()

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inv1.id,
                    "quantity_boxes": 2,
                    "price": "100.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text

    added = auth_client.post(
        f"/api/sales/{sale_id}/lines",
        json={
            "inventory_id": inv2.id,
            "quantity_boxes": 1,
            "price": "50.00",
            "price_type": "BOX",
        },
    )
    assert added.status_code == 201, added.text
    added_line = added.json()
    assert added_line["quantity_boxes"] == 1

    db_session.expire_all()
    inv2_after_add = db_session.get(Inventory, inv2.id)
    assert inv2_after_add is not None
    assert inv2_after_add.stock == 59

    deleted = auth_client.delete(f"/api/sales/{sale_id}/lines/{added_line['id']}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["is_active"] is False

    db_session.expire_all()
    inv2_after_delete = db_session.get(Inventory, inv2.id)
    assert inv2_after_delete is not None
    assert inv2_after_delete.stock == 60


def test_sales_metrics_ignore_reversed_history_and_use_latest_effective_value(
    auth_client, db_session
):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=20)
    sale_price = Decimal("5.00")

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inventory.id,
                    "quantity_boxes": 2,
                    "price": str(sale_price),
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    sale_id = sale["id"]
    sale_line_id = sale["lines"][0]["id"]

    paid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text

    first_metrics = auth_client.get(
        "/api/products/list-stock",
        params={"warehouse_id": inventory.warehouse_id},
    )
    assert first_metrics.status_code == 200, first_metrics.text
    first_item = first_metrics.json()[0]["inventory"][0]
    assert first_item["sales_last_price"] == 5.0
    assert first_item["sales_avg_price"] == 5.0

    reverted = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "DRAFT"},
    )
    assert reverted.status_code == 200, reverted.text

    reverted_metrics = auth_client.get(
        "/api/products/list-stock",
        params={"warehouse_id": inventory.warehouse_id},
    )
    assert reverted_metrics.status_code == 200, reverted_metrics.text
    reverted_item = reverted_metrics.json()[0]["inventory"][0]
    assert reverted_item["sales_last_price"] is None
    assert reverted_item["sales_avg_price"] is None

    updated = auth_client.put(
        f"/api/sales/{sale_id}/lines/{sale_line_id}",
        json={"price": "7.00", "price_type": "BOX"},
    )
    assert updated.status_code == 200, updated.text

    repaid = auth_client.put(
        f"/api/sales/update-status/{sale_id}",
        json={"status": "PAID"},
    )
    assert repaid.status_code == 200, repaid.text

    latest_metrics = auth_client.get(
        "/api/products/list-stock",
        params={"warehouse_id": inventory.warehouse_id},
    )
    assert latest_metrics.status_code == 200, latest_metrics.text
    latest_item = latest_metrics.json()[0]["inventory"][0]
    assert latest_item["sales_last_price"] == 7.0
    assert latest_item["sales_avg_price"] == 7.0

    movements = (
        db_session.exec(
            select(InventoryMovement)
            .where(InventoryMovement.sale_line_id == sale_line_id)
            .order_by(InventoryMovement.id)
        ).all()
    )
    assert len(movements) == 9
    assert all(movement.is_active for movement in movements)
    assert [movement.event_type.value for movement in movements] == [
        "SALE_RESERVED",
        "SALE_RELEASED",
        "SALE_APPROVED",
        "SALE_REVERSED",
        "SALE_RESERVED",
        "SALE_RELEASED",
        "SALE_RESERVED",
        "SALE_RELEASED",
        "SALE_APPROVED",
    ]


def test_draft_sale_allows_zero_price_but_paid_rejects_it(
    auth_client, db_session
):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=6)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_boxes": 2, "price": "0.00"}],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    assert Decimal(str(sale["total_price"])) == Decimal("0.00")
    assert sale["lines"][0]["reservation_applied"] is True

    db_session.expire_all()
    inv = db_session.get(Inventory, inventory.id)
    assert inv is not None
    assert inv.stock == 6
    assert inv.reserved_stock == 2

    paid = auth_client.put(
        f"/api/sales/update-status/{sale['id']}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 409, paid.text
    assert (
        paid.json()["message"]
        == "No se puede marcar la venta como pagada con líneas de precio cero."
    )


def test_sale_tracks_creator_payer_and_canceller(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=5)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [{"inventory_id": inventory.id, "quantity_boxes": 1, "price": "10.00"}],
        },
    )
    assert created.status_code == 201, created.text
    created_sale = created.json()
    assert created_sale["created_by"] is not None
    assert created_sale["created_by_name"]

    paid = auth_client.put(
        f"/api/sales/update-status/{created_sale['id']}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    paid_sale = paid.json()
    assert paid_sale["paid_by"] is not None
    assert paid_sale["paid_by_name"]
    assert paid_sale["paid_at"] is not None

    cancelled = auth_client.put(
        f"/api/sales/update-status/{created_sale['id']}",
        json={"status": "CANCELLED"},
    )
    assert cancelled.status_code == 200, cancelled.text
    cancelled_sale = cancelled.json()
    assert cancelled_sale["cancelled_by"] is not None
    assert cancelled_sale["cancelled_by_name"]
    assert cancelled_sale["cancelled_at"] is not None


def test_piece_sale_projects_box_opening_in_draft_and_executes_it_on_paid(
    auth_client, db_session
):
    category = Category(name="Category Piezas")
    brand = Brand(name="Brand Piezas")
    warehouse = Warehouse(
        name="Warehouse Piezas",
        address="Some address",
        email="warehouse.piezas@example.com",
        phone="+521234567891",
    )
    client_obj = Client(name="Client Piezas", email="client.piezas@example.com", phone=None)

    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Producto por pieza",
        code="PROD-PIEZA-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(product)
    db_session.refresh(client_obj)

    box_inventory = Inventory(
        stock=2,
        reserved_stock=0,
        box_size=12,
        avg_cost=Decimal("120.00"),
        last_cost=Decimal("120.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    db_session.add(box_inventory)
    db_session.commit()
    db_session.refresh(box_inventory)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": box_inventory.id,
                    "quantity_units": 5,
                    "price": "10.00",
                    "price_type": "UNIT",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    line = sale["lines"][0]
    assert line["quantity_mode"] == "UNIT"
    assert line["box_size"] == 1
    assert line["quantity_boxes"] == 5
    assert line["inventory_id"] == box_inventory.id
    assert line["reservation_applied"] is True
    assert line["source_box_size"] == 12
    assert line["projected_units_from_stock"] == 0
    assert line["projected_boxes_to_open"] == 1
    assert line["projected_units_leftover"] == 7

    db_session.expire_all()
    source_inventory = db_session.get(Inventory, box_inventory.id)
    unit_inventory = db_session.exec(
        select(Inventory).where(
            Inventory.warehouse_id == warehouse.id,
            Inventory.product_id == product.id,
            Inventory.box_size == 1,
        )
    ).first()
    assert source_inventory is not None
    assert unit_inventory is not None
    assert source_inventory.stock == 2
    assert unit_inventory.box_size == 1
    assert unit_inventory.stock == 0
    assert unit_inventory.reserved_stock == 5

    movements = db_session.exec(
        select(InventoryMovement)
        .where(InventoryMovement.sale_line_id == line["id"])
        .order_by(InventoryMovement.id)
    ).all()
    assert [movement.event_type.value for movement in movements] == ["SALE_RESERVED"]

    paid = auth_client.put(
        f"/api/sales/update-status/{sale['id']}",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text

    db_session.expire_all()
    source_inventory = db_session.get(Inventory, box_inventory.id)
    unit_inventory = db_session.get(Inventory, unit_inventory.id)
    assert source_inventory is not None
    assert unit_inventory is not None
    assert source_inventory.stock == 1
    assert unit_inventory.stock == 7
    assert unit_inventory.reserved_stock == 0

    movements = db_session.exec(
        select(InventoryMovement)
        .where(InventoryMovement.sale_line_id == line["id"])
        .order_by(InventoryMovement.id)
    ).all()
    assert [movement.event_type.value for movement in movements] == [
        "SALE_RESERVED",
        "SALE_RELEASED",
        "BOX_OPENED_OUT",
        "BOX_OPENED_IN",
        "SALE_APPROVED",
    ]


def test_sale_can_mix_box_and_piece_lines_from_same_source_inventory(
    auth_client, db_session
):
    category = Category(name="Category Mixta")
    brand = Brand(name="Brand Mixta")
    warehouse = Warehouse(
        name="Warehouse Mixta",
        address="Some address",
        email="warehouse.mixta@example.com",
        phone="+521234567893",
    )
    client_obj = Client(name="Client Mixta", email="client.mixta@example.com", phone=None)

    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Producto mixto",
        code="PROD-MIX-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(product)
    db_session.refresh(client_obj)

    box_inventory = Inventory(
        stock=6,
        reserved_stock=0,
        box_size=3,
        avg_cost=Decimal("30.00"),
        last_cost=Decimal("30.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    db_session.add(box_inventory)
    db_session.commit()
    db_session.refresh(box_inventory)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": box_inventory.id,
                    "quantity_boxes": 1,
                    "price": "40.00",
                    "price_type": "BOX",
                },
                {
                    "inventory_id": box_inventory.id,
                    "quantity_units": 10,
                    "price": "15.00",
                    "price_type": "UNIT",
                },
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()
    assert len(sale["lines"]) == 2
    assert {line["quantity_mode"] for line in sale["lines"]} == {"BOX", "UNIT"}


def test_piece_sale_projection_uses_existing_unit_stock(auth_client, db_session):
    category = Category(name="Category Proyeccion")
    brand = Brand(name="Brand Proyeccion")
    warehouse = Warehouse(
        name="Warehouse Proyeccion",
        address="Some address",
        email="warehouse.proyeccion@example.com",
        phone="+521234567894",
    )
    client_obj = Client(
        name="Client Proyeccion",
        email="client.proyeccion@example.com",
        phone=None,
    )

    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Producto proyeccion",
        code="PROD-PROY-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(product)
    db_session.refresh(client_obj)

    box_inventory = Inventory(
        stock=5,
        reserved_stock=0,
        box_size=3,
        avg_cost=Decimal("30.00"),
        last_cost=Decimal("30.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    unit_inventory = Inventory(
        stock=4,
        reserved_stock=0,
        box_size=1,
        avg_cost=Decimal("10.00"),
        last_cost=Decimal("10.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    db_session.add(box_inventory)
    db_session.add(unit_inventory)
    db_session.commit()
    db_session.refresh(box_inventory)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": box_inventory.id,
                    "quantity_units": 10,
                    "price": "12.00",
                    "price_type": "UNIT",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    line = created.json()["lines"][0]
    assert line["projected_units_from_stock"] == 4
    assert line["projected_boxes_to_open"] == 2
    assert line["projected_units_leftover"] == 0
