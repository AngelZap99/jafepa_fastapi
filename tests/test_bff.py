from src.shared.models.product.product_model import Product


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
