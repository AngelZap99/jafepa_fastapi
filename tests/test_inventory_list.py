def test_inventory_list_supports_filter_by_warehouse_name_and_id(client, db_session):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.inventory.inventory_model import Inventory
    from src.shared.models.product.product_model import Product
    from src.shared.models.warehouse.warehouse_model import Warehouse

    category = Category(name="Category List", description="Root", parent_id=None)
    brand = Brand(name="Brand List")
    warehouse_a = Warehouse(
        name="Almacen Norte",
        address="Direccion Norte",
        email="north@example.com",
        phone="+521111111111",
    )
    warehouse_b = Warehouse(
        name="Almacen Sur",
        address="Direccion Sur",
        email="south@example.com",
        phone="+521222222222",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse_a)
    db_session.add(warehouse_b)
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(brand)
    db_session.refresh(warehouse_a)
    db_session.refresh(warehouse_b)

    product = Product(
        name="Bocina RINO",
        code="BR-LIST",
        description="Producto de prueba",
        category_id=category.id,
        subcategory_id=None,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    inventory_a = Inventory(
        stock=5,
        box_size=1,
        avg_cost=100.0,
        last_cost=120.0,
        warehouse_id=warehouse_a.id,
        product_id=product.id,
        is_active=True,
    )
    inventory_b = Inventory(
        stock=9,
        box_size=1,
        avg_cost=100.0,
        last_cost=120.0,
        warehouse_id=warehouse_b.id,
        product_id=product.id,
        is_active=True,
    )
    db_session.add(inventory_a)
    db_session.add(inventory_b)
    db_session.commit()
    db_session.refresh(inventory_a)
    db_session.refresh(inventory_b)

    by_name = client.get("/api/inventory/list", params={"almacen": warehouse_a.name})
    assert by_name.status_code == 200, by_name.text
    by_name_ids = {item["id"] for item in by_name.json()}
    assert inventory_a.id in by_name_ids
    assert inventory_b.id not in by_name_ids

    by_id = client.get("/api/inventory/list", params={"almacen": warehouse_b.id})
    assert by_id.status_code == 200, by_id.text
    by_id_ids = {item["id"] for item in by_id.json()}
    assert inventory_b.id in by_id_ids
    assert inventory_a.id not in by_id_ids
