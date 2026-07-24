from datetime import date
from decimal import Decimal

from src.shared.enums.sale_enums import (
    SaleLinePriceType,
    SaleLineQuantityMode,
    SaleStatus,
)
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.product.product_model import Product
from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine


def test_system_summary_returns_200_and_catalog_counts(auth_client, db_session, catalog_seed):
    product = Product(
        name="Product Summary",
        code="SUMMARY-001",
        description="Product used for BFF summary test",
        category_id=catalog_seed["category_id"],
        brand_id=catalog_seed["brand_id"],
        image=None,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    response = auth_client.get("/api/bff/system-summary", params={"days": 14})

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["days"] == 14
    assert payload["catalogs"]["products"] >= 1
    assert payload["catalogs"]["clients"] >= 1
    assert payload["catalogs"]["warehouses"] >= 1
    assert payload["catalogs"]["categories"] >= 1
    assert payload["catalogs"]["brands"] >= 1
    assert "generated_at" in payload


def test_system_summary_returns_sales_metrics_and_normalized_product_flow(
    auth_client,
    db_session,
    catalog_seed,
):
    high_flow_product = Product(
        name="High Flow Product",
        code="FLOW-HIGH",
        description=None,
        category_id=catalog_seed["category_id"],
        brand_id=catalog_seed["brand_id"],
        image=None,
        is_active=True,
    )
    low_flow_product = Product(
        name="Low Flow Product",
        code="FLOW-LOW",
        description=None,
        category_id=catalog_seed["category_id"],
        brand_id=catalog_seed["brand_id"],
        image=None,
        is_active=True,
    )
    no_flow_product = Product(
        name="No Flow Product",
        code="FLOW-NONE",
        description=None,
        category_id=catalog_seed["category_id"],
        brand_id=catalog_seed["brand_id"],
        image=None,
        is_active=True,
    )
    db_session.add_all([high_flow_product, low_flow_product, no_flow_product])
    db_session.commit()
    for product in [high_flow_product, low_flow_product, no_flow_product]:
        db_session.refresh(product)

    high_flow_inventory = Inventory(
        stock=8,
        reserved_stock=0,
        box_size=12,
        avg_cost=Decimal("50.00"),
        last_cost=Decimal("50.00"),
        warehouse_id=catalog_seed["warehouse_id"],
        product_id=high_flow_product.id,
        is_active=True,
    )
    low_flow_inventory = Inventory(
        stock=0,
        reserved_stock=0,
        box_size=1,
        avg_cost=Decimal("5.00"),
        last_cost=Decimal("5.00"),
        warehouse_id=catalog_seed["warehouse_id"],
        product_id=low_flow_product.id,
        is_active=True,
    )
    db_session.add_all([high_flow_inventory, low_flow_inventory])
    db_session.commit()
    db_session.refresh(high_flow_inventory)
    db_session.refresh(low_flow_inventory)

    high_flow_sale = Sale(
        sale_date=date.today(),
        status=SaleStatus.PAID,
        total_price=Decimal("240.00"),
        client_id=catalog_seed["client_id"],
        is_active=True,
    )
    low_flow_sale = Sale(
        sale_date=date.today(),
        status=SaleStatus.PAID,
        total_price=Decimal("30.00"),
        client_id=catalog_seed["client_id"],
        is_active=True,
    )
    db_session.add_all([high_flow_sale, low_flow_sale])
    db_session.commit()
    db_session.refresh(high_flow_sale)
    db_session.refresh(low_flow_sale)

    db_session.add_all(
        [
            SaleLine(
                sale_id=high_flow_sale.id,
                inventory_id=high_flow_inventory.id,
                quantity_units=2,
                box_size=12,
                price=Decimal("120.00"),
                price_type=SaleLinePriceType.BOX,
                quantity_mode=SaleLineQuantityMode.BOX,
                unit_price=Decimal("10.00"),
                box_price=Decimal("120.00"),
                total_price=Decimal("240.00"),
                product_code=high_flow_product.code,
                product_name=high_flow_product.name,
                is_active=True,
            ),
            SaleLine(
                sale_id=low_flow_sale.id,
                inventory_id=low_flow_inventory.id,
                quantity_units=3,
                box_size=1,
                price=Decimal("10.00"),
                price_type=SaleLinePriceType.UNIT,
                quantity_mode=SaleLineQuantityMode.UNIT,
                unit_price=Decimal("10.00"),
                box_price=Decimal("10.00"),
                total_price=Decimal("30.00"),
                product_code=low_flow_product.code,
                product_name=low_flow_product.name,
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    response = auth_client.get(
        "/api/bff/system-summary",
        params={"days": 30, "flow_months": 6},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["days"] == 30
    assert payload["sales"]["paid_last_n_days"] == 2
    assert Decimal(payload["sales"]["revenue_last_n_days"]) == Decimal("270.00")
    assert Decimal(payload["sales"]["average_ticket_last_n_days"]) == Decimal(
        "135.00"
    )
    assert payload["product_flow"]["months"] == 6
    assert payload["product_flow"]["products_without_sales"] >= 1

    top_product = payload["product_flow"]["top_products"][0]
    assert top_product["product_code"] == high_flow_product.code
    assert top_product["units_sold"] == 24
    assert top_product["sales_count"] == 1
    assert Decimal(top_product["average_units_per_sale"]) == Decimal("24.0")

    assert any(
        product["units_sold"] == 0
        for product in payload["product_flow"]["low_products"]
    )
    assert payload["inventory"]["products_without_availability"] >= 2
    assert len(payload["monthly_sales"]) == 6
    assert payload["monthly_sales"][-1]["sales_count"] == 2
    assert payload["monthly_sales"][-1]["units_sold"] == 27
    assert Decimal(payload["monthly_sales"][-1]["total_amount"]) == Decimal(
        "270.00"
    )

    flow_response = auth_client.get(
        "/api/bff/product-flow",
        params={
            "months": 6,
            "sort_by": "units",
            "order": "desc",
            "limit": 10,
        },
    )
    assert flow_response.status_code == 200, flow_response.text
    flow_payload = flow_response.json()
    assert flow_payload["total"] == 3
    assert flow_payload["items"][0]["product_code"] == high_flow_product.code
    assert flow_payload["items"][0]["units_rank"] == 1
    assert flow_payload["items"][0]["sales_rank"] == 1
    assert Decimal(flow_payload["items"][0]["mixed_score"]) == Decimal("75.0")
    assert flow_payload["items"][-1]["product_code"] == no_flow_product.code

    search_response = auth_client.get(
        "/api/bff/product-flow",
        params={"search": "flow-high", "sort_by": "mixed"},
    )
    assert search_response.status_code == 200, search_response.text
    search_payload = search_response.json()
    assert search_payload["total"] == 1
    assert search_payload["items"][0]["product_id"] == high_flow_product.id
    assert search_payload["items"][0]["units_rank"] == 1
