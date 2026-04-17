from datetime import date
from decimal import Decimal

from sqlmodel import select

from src.shared.enums.inventory_enums import InventoryValueType
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import InventoryMovement
from src.shared.models.product.product_model import Product


def test_invoice_create_supports_optional_dates_general_expenses_and_unit_price(
    client, db_session, catalog_seed
):
    from src.shared.models.category.category_model import Category
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    warehouse = db_session.get(Warehouse, catalog_seed["warehouse_id"])
    assert category is not None
    assert brand is not None
    assert warehouse is not None

    product = Product(
        name="Taladro de prueba",
        code="TAL-001",
        description="Taladro industrial",
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0001",
            "sequence": 1,
            "status": "DRAFT",
            "warehouse_id": warehouse.id,
            "general_expenses": "15.00",
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 12,
                    "quantity_boxes": 2,
                    "price": "10.00",
                    "price_type": "UNIT",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["invoice_number"] == "INV-0001"
    assert data["sequence"] == 1
    assert data["status"] == "DRAFT"
    assert data["invoice_date"] == date.today().isoformat()
    assert data["order_date"] is None
    assert data["arrival_date"] is None
    assert Decimal(str(data["general_expenses"])) == Decimal("15.00")
    assert Decimal(str(data["subtotal"])) == Decimal("240.00")
    assert Decimal(str(data["general_expenses_total"])) == Decimal("36.00")
    assert Decimal(str(data["approximate_profit_total"])) == Decimal("0.00")
    assert Decimal(str(data["total"])) == Decimal("276.00")

    line = data["lines"][0]
    assert line["price_type"] == "UNIT"
    assert Decimal(str(line["price"])) == Decimal("120.00")
    assert Decimal(str(line["box_price"])) == Decimal("120.00")
    assert Decimal(str(line["unit_price"])) == Decimal("10.00")
    assert Decimal(str(line["total_price"])) == Decimal("240.00")


def test_invoice_update_accepts_general_expenses_field(client, catalog_seed):
    created = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0002",
            "sequence": 2,
            "status": "DRAFT",
            "warehouse_id": catalog_seed["warehouse_id"],
        },
    )

    assert created.status_code == 201, created.text

    invoice_id = created.json()["id"]

    updated = client.put(
        f"/api/invoices/update/{invoice_id}",
        json={"general_expenses": "12.50"},
    )

    assert updated.status_code == 200, updated.text
    data = updated.json()
    assert Decimal(str(data["general_expenses"])) == Decimal("12.50")
    assert Decimal(str(data["subtotal"])) == Decimal("0.00")
    assert Decimal(str(data["general_expenses_total"])) == Decimal("0.00")
    assert Decimal(str(data["approximate_profit_total"])) == Decimal("0.00")
    assert Decimal(str(data["total"])) == Decimal("0.00")


def test_arrived_invoice_registers_cost_movements(client, db_session, catalog_seed):
    from src.shared.models.category.category_model import Category
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    warehouse = db_session.get(Warehouse, catalog_seed["warehouse_id"])
    assert category is not None
    assert brand is not None
    assert warehouse is not None

    product = Product(
        name="Producto factura costo",
        code="FAC-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0003",
            "sequence": 3,
            "status": "ARRIVED",
            "warehouse_id": warehouse.id,
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 6,
                    "quantity_boxes": 2,
                    "price": "25.00",
                    "price_type": "BOX",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    invoice = response.json()
    line_id = invoice["lines"][0]["id"]

    movement = (
        db_session.exec(
            select(InventoryMovement).where(InventoryMovement.invoice_line_id == line_id)
        ).one()
    )
    assert movement.value_type == InventoryValueType.COST
    assert movement.unit_value == Decimal("25.00")


def test_invoice_reversal_keeps_full_history_active_and_reapplies(client, db_session, catalog_seed):
    from src.shared.models.category.category_model import Category
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    warehouse = db_session.get(Warehouse, catalog_seed["warehouse_id"])
    assert category is not None
    assert brand is not None
    assert warehouse is not None

    product = Product(
        name="Producto reversa factura",
        code="FAC-REV-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    created = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0004",
            "sequence": 4,
            "status": "ARRIVED",
            "warehouse_id": warehouse.id,
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 4,
                    "quantity_boxes": 2,
                    "price": "11.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    invoice = created.json()
    invoice_id = invoice["id"]
    line_id = invoice["lines"][0]["id"]

    reverted = client.put(
        f"/api/invoices/update-status/{invoice_id}",
        json={"status": "DRAFT"},
    )
    assert reverted.status_code == 200, reverted.text

    reapplied = client.put(
        f"/api/invoices/update-status/{invoice_id}",
        json={"status": "ARRIVED"},
    )
    assert reapplied.status_code == 200, reapplied.text

    db_session.expire_all()
    movements = (
        db_session.exec(
            select(InventoryMovement)
            .where(InventoryMovement.invoice_line_id == line_id)
            .order_by(InventoryMovement.id)
        ).all()
    )
    assert len(movements) == 3
    assert all(movement.is_active for movement in movements)
    assert [movement.event_type.value for movement in movements] == [
        "INVOICE_RECEIVED",
        "INVOICE_UNRECEIVED",
        "INVOICE_RECEIVED",
    ]

    movement_payload = client.get(
        "/api/inventory/movements",
        params={"invoice_line_id": line_id},
    )
    assert movement_payload.status_code == 200, movement_payload.text
    listed = movement_payload.json()
    assert len(listed) == 3
    assert all("unit_value" in item for item in listed)
    assert all("unit_cost" not in item for item in listed)


def test_invoice_reversal_recomputes_inventory_costs_from_effective_history(
    client, db_session, catalog_seed
):
    from src.shared.models.category.category_model import Category
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    warehouse = db_session.get(Warehouse, catalog_seed["warehouse_id"])
    assert category is not None
    assert brand is not None
    assert warehouse is not None

    product = Product(
        name="Producto costo efectivo",
        code="FAC-REV-002",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    first = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0005",
            "sequence": 5,
            "status": "ARRIVED",
            "warehouse_id": warehouse.id,
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 1,
                    "quantity_boxes": 1,
                    "price": "10.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0006",
            "sequence": 6,
            "status": "ARRIVED",
            "warehouse_id": warehouse.id,
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 1,
                    "quantity_boxes": 1,
                    "price": "20.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert second.status_code == 201, second.text

    inventory = db_session.exec(
        select(Inventory).where(
            Inventory.warehouse_id == warehouse.id,
            Inventory.product_id == product.id,
            Inventory.box_size == 1,
        )
    ).one()
    assert inventory.avg_cost == Decimal("15.00")
    assert inventory.last_cost == Decimal("20.00")

    reverted = client.put(
        f"/api/invoices/update-status/{second.json()['id']}",
        json={"status": "DRAFT"},
    )
    assert reverted.status_code == 200, reverted.text

    db_session.expire_all()
    inventory = db_session.exec(
        select(Inventory).where(
            Inventory.warehouse_id == warehouse.id,
            Inventory.product_id == product.id,
            Inventory.box_size == 1,
        )
    ).one()
    assert inventory.stock == 1
    assert inventory.avg_cost == Decimal("10.00")
    assert inventory.last_cost == Decimal("10.00")
