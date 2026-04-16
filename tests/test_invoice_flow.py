from datetime import date
from decimal import Decimal

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
