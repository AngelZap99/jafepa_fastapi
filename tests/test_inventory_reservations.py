from datetime import date
from decimal import Decimal

from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.client.client_model import Client
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.product.product_model import Product
from src.shared.models.warehouse.warehouse_model import Warehouse


def _seed_inventory_and_client(db_session, *, stock: int = 10) -> tuple[Inventory, Client]:
    category = Category(name="Category Reservation")
    brand = Brand(name="Brand Reservation")
    warehouse = Warehouse(
        name="Main warehouse reservation",
        address="Some address",
        email="warehouse.reservation@example.com",
        phone="+521234567892",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Product Reservation",
        code="PROD-RES-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    client = Client(name="Client Reservation", email="client.reservation@example.com", phone=None)
    db_session.add(product)
    db_session.add(client)
    db_session.commit()

    inventory = Inventory(
        stock=stock,
        reserved_stock=0,
        box_size=1,
        avg_cost=Decimal("1.00"),
        last_cost=Decimal("1.00"),
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)
    db_session.refresh(client)
    return inventory, client


def test_inventory_detail_lists_active_reservations(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=8)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "notes": "apartado activo",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inventory.id,
                    "quantity_boxes": 3,
                    "price": "50.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    sale = created.json()

    detail = auth_client.get(f"/api/inventory/{inventory.id}")
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert payload["stock"] == 8
    assert payload["reserved_stock"] == 3
    assert payload["available_stock"] == 5
    assert payload["is_over_reserved"] is False
    assert len(payload["active_reservations"]) == 1
    reservation = payload["active_reservations"][0]
    assert reservation["sale_id"] == sale["id"]
    assert reservation["sale_line_id"] == sale["lines"][0]["id"]
    assert reservation["quantity_boxes"] == 3
    assert reservation["sale"]["status"] == "DRAFT"
    assert reservation["sale"]["client"]["id"] == client_obj.id


def test_product_stock_bff_exposes_reserved_and_available_boxes(auth_client, db_session):
    inventory, client_obj = _seed_inventory_and_client(db_session, stock=8)

    created = auth_client.post(
        "/api/sales/create",
        json={
            "sale_date": date.today().isoformat(),
            "status": "DRAFT",
            "client_id": client_obj.id,
            "lines": [
                {
                    "inventory_id": inventory.id,
                    "quantity_boxes": 5,
                    "price": "25.00",
                    "price_type": "BOX",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text

    stock = auth_client.get(
        "/api/products/list-stock",
        params={"warehouse_id": inventory.warehouse_id},
    )
    assert stock.status_code == 200, stock.text
    item = stock.json()[0]["inventory"][0]
    assert item["stock"] == 8
    assert item["reserved_stock"] == 5
    assert item["available_boxes"] == 3
    assert item["is_over_reserved"] is False


def test_inventory_detail_projects_piece_reservations(auth_client, db_session):
    category = Category(name="Category Reservation Pieces")
    brand = Brand(name="Brand Reservation Pieces")
    warehouse = Warehouse(
        name="Warehouse Reservation Pieces",
        address="Some address",
        email="warehouse.reservation.pieces@example.com",
        phone="+521234567895",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()

    product = Product(
        name="Product Reservation Pieces",
        code="PROD-RES-PIECES-001",
        description=None,
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    client_obj = Client(
        name="Client Reservation Pieces",
        email="client.reservation.pieces@example.com",
        phone=None,
    )
    db_session.add(product)
    db_session.add(client_obj)
    db_session.commit()

    box_inventory = Inventory(
        stock=3,
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
    db_session.refresh(unit_inventory)
    db_session.refresh(client_obj)

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
                    "price": "15.00",
                    "price_type": "UNIT",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text

    detail = auth_client.get(f"/api/inventory/{box_inventory.id}")
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert len(payload["active_reservations"]) == 1
    reservation = payload["active_reservations"][0]
    assert reservation["quantity_mode"] == "UNIT"
    assert reservation["source_box_size"] == 3
    assert reservation["projected_units_from_stock"] == 4
    assert reservation["projected_boxes_to_open"] == 2
    assert reservation["projected_units_leftover"] == 0
