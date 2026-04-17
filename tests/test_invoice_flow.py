from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from src.shared.enums.inventory_enums import InventoryValueType
from src.shared.enums.invoice_enums import InvoiceStatus
from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
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


def test_arrived_invoice_is_idempotent_when_status_is_repeated(
    client, db_session, catalog_seed
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    warehouse = db_session.get(Warehouse, catalog_seed["warehouse_id"])
    assert category is not None
    assert brand is not None
    assert warehouse is not None

    product = Product(
        name="Producto arrived idempotente",
        code="FAC-IDEM-001",
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
            "invoice_number": "INV-0007",
            "sequence": 7,
            "status": "DRAFT",
            "warehouse_id": warehouse.id,
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 3,
                    "quantity_boxes": 2,
                    "price": "14.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]
    line_id = created.json()["lines"][0]["id"]

    first = client.put(
        f"/api/invoices/update-status/{invoice_id}",
        json={"status": "ARRIVED"},
    )
    assert first.status_code == 200, first.text

    second = client.put(
        f"/api/invoices/update-status/{invoice_id}",
        json={"status": "ARRIVED"},
    )
    assert second.status_code == 200, second.text

    db_session.expire_all()
    movements = db_session.exec(
        select(InventoryMovement).where(InventoryMovement.invoice_line_id == line_id)
    ).all()
    assert len(movements) == 1

    inventory = db_session.exec(
        select(Inventory).where(
            Inventory.warehouse_id == warehouse.id,
            Inventory.product_id == product.id,
            Inventory.box_size == 3,
        )
    ).one()
    assert inventory.stock == 2


def test_invoice_line_create_rejects_duplicate_product_and_box_size(
    client, db_session, catalog_seed
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    assert category is not None
    assert brand is not None

    product = Product(
        name="Producto línea duplicada create",
        code="FAC-DUP-001",
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
            "invoice_number": "INV-0008",
            "sequence": 8,
            "status": "DRAFT",
            "warehouse_id": catalog_seed["warehouse_id"],
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 6,
                    "quantity_boxes": 1,
                    "price": "18.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    duplicate = client.post(
        f"/api/invoice-lines/create/{invoice_id}",
        json={
            "product_id": product.id,
            "box_size": 6,
            "quantity_boxes": 3,
            "price": "19.00",
            "price_type": "BOX",
        },
    )
    assert duplicate.status_code == 409, duplicate.text
    body = duplicate.json()
    assert (
        "No se permite repetir la combinación de producto y tamaño de caja"
        in body["message"]
    )


def test_invoice_line_update_rejects_duplicate_product_and_box_size(
    client, db_session, catalog_seed
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    assert category is not None
    assert brand is not None

    product = Product(
        name="Producto línea duplicada update",
        code="FAC-DUP-002",
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
            "invoice_number": "INV-0009",
            "sequence": 9,
            "status": "DRAFT",
            "warehouse_id": catalog_seed["warehouse_id"],
            "lines": [
                {
                    "product_id": product.id,
                    "box_size": 6,
                    "quantity_boxes": 1,
                    "price": "18.00",
                    "price_type": "BOX",
                },
                {
                    "product_id": product.id,
                    "box_size": 12,
                    "quantity_boxes": 1,
                    "price": "24.00",
                    "price_type": "BOX",
                },
            ],
        },
    )
    assert created.status_code == 201, created.text
    invoice = created.json()
    line_id = invoice["lines"][1]["id"]

    duplicate = client.put(
        f"/api/invoice-lines/update/{invoice['id']}/{line_id}",
        json={"box_size": 6},
    )
    assert duplicate.status_code == 409, duplicate.text
    body = duplicate.json()
    assert (
        "No se permite repetir la combinación de producto y tamaño de caja"
        in body["message"]
    )


def test_invoice_line_db_constraint_blocks_duplicate_active_keys(
    db_session, catalog_seed
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category

    category = db_session.get(Category, catalog_seed["category_id"])
    brand = db_session.get(Brand, catalog_seed["brand_id"])
    assert category is not None
    assert brand is not None

    product = Product(
        name="Producto constraint invoice line",
        code="FAC-DUP-DB-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    invoice = Invoice(
        invoice_number="INV-0010",
        sequence=10,
        status=InvoiceStatus.DRAFT,
        warehouse_id=catalog_seed["warehouse_id"],
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)

    line_one = InvoiceLine(
        invoice_id=invoice.id,
        product_id=product.id,
        box_size=8,
        quantity_boxes=1,
        total_units=8,
        price=Decimal("10.00"),
    )
    line_two = InvoiceLine(
        invoice_id=invoice.id,
        product_id=product.id,
        box_size=8,
        quantity_boxes=2,
        total_units=16,
        price=Decimal("11.00"),
    )

    db_session.add(line_one)
    db_session.commit()

    db_session.add(line_two)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invoice_can_create_inline_product_and_receive_inventory(
    client, db_session, catalog_seed
):
    response = client.post(
        "/api/invoices/create",
        json={
            "invoice_number": "INV-0011",
            "sequence": 11,
            "status": "ARRIVED",
            "warehouse_id": catalog_seed["warehouse_id"],
            "lines": [
                {
                    "new_product": {
                        "name": "Producto inline factura",
                        "code": "FAC-INLINE-001",
                        "description": "Creado desde factura",
                        "category_id": catalog_seed["category_id"],
                        "brand_id": catalog_seed["brand_id"],
                    },
                    "box_size": 10,
                    "quantity_boxes": 2,
                    "price": "35.00",
                    "price_type": "BOX",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    invoice = response.json()
    line = invoice["lines"][0]
    assert line["product_id"] > 0

    product = db_session.exec(
        select(Product).where(Product.code == "FAC-INLINE-001")
    ).first()
    assert product is not None
    assert product.id == line["product_id"]

    inventory = db_session.exec(
        select(Inventory).where(
            Inventory.warehouse_id == catalog_seed["warehouse_id"],
            Inventory.product_id == product.id,
            Inventory.box_size == 10,
        )
    ).first()
    assert inventory is not None
    assert inventory.stock == 2
