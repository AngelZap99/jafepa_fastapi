from decimal import Decimal
from types import SimpleNamespace

from src.modules.inventory.domain.pdf_generator import PDFGenerator
from src.modules.inventory.domain.inventory_repository import InventoryRepository


def test_inventory_pdf_all_supports_combined_filters_without_500(
    client, db_session, monkeypatch
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.inventory.inventory_model import Inventory
    from src.shared.models.product.product_model import Product
    from src.shared.models.warehouse.warehouse_model import Warehouse

    captured = {}

    def fake_generate_inventory_pdf(self, items, warehouse=None):
        captured["items"] = items
        captured["warehouse"] = warehouse
        return b"%PDF-1.4 test pdf"

    monkeypatch.setattr(
        PDFGenerator,
        "generate_inventory_pdf",
        fake_generate_inventory_pdf,
        raising=True,
    )

    category = Category(name="Categoria PDF", description="Root")
    brand = Brand(name="Marca PDF")
    warehouse = Warehouse(
        name="Warehouse PDF",
        address="PDF address",
        email="warehouse.pdf@example.com",
        phone="+521111111111",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(brand)
    db_session.refresh(warehouse)

    matching_product = Product(
        name="Bocina RINO",
        code="BR-100",
        description="Producto incluido",
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    other_product = Product(
        name="Otro Producto",
        code="OT-200",
        description="Producto excluido",
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(matching_product)
    db_session.add(other_product)
    db_session.commit()
    db_session.refresh(matching_product)
    db_session.refresh(other_product)

    matching_inventory = Inventory(
        stock=8,
        box_size=2,
        avg_cost=Decimal("10.50"),
        last_cost=Decimal("11.00"),
        warehouse_id=warehouse.id,
        product_id=matching_product.id,
        is_active=True,
    )
    other_inventory = Inventory(
        stock=3,
        box_size=1,
        avg_cost=Decimal("5.00"),
        last_cost=Decimal("5.50"),
        warehouse_id=warehouse.id,
        product_id=other_product.id,
        is_active=True,
    )
    db_session.add(matching_inventory)
    db_session.add(other_inventory)
    db_session.commit()
    db_session.refresh(matching_inventory)
    db_session.refresh(other_inventory)

    response = client.get(
        "/api/inventory/pdf/all",
        params={
            "almacen": warehouse.name,
            "categoria": category.name,
            "marca": brand.name,
            "buscar": "rino",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 test pdf"

    items = captured["items"]
    assert len(items) == 1
    assert items[0].id == matching_inventory.id
    assert items[0].product.name == "Bocina RINO"
    assert captured["warehouse"] is not None
    assert captured["warehouse"].id == warehouse.id
    assert captured["warehouse"].name == warehouse.name


def test_inventory_pdf_without_warehouse_filter_uses_selected_item_warehouse(
    client, db_session, monkeypatch
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.inventory.inventory_model import Inventory
    from src.shared.models.product.product_model import Product
    from src.shared.models.warehouse.warehouse_model import Warehouse

    captured = {}

    def fake_generate_inventory_pdf(self, items, warehouse=None):
        captured["items"] = items
        captured["warehouse"] = warehouse
        return b"%PDF-1.4 test pdf"

    monkeypatch.setattr(
        PDFGenerator,
        "generate_inventory_pdf",
        fake_generate_inventory_pdf,
        raising=True,
    )

    category = Category(name="Categoria PDF Fallback", description="Root")
    brand = Brand(name="Marca PDF Fallback")
    warehouse_a = Warehouse(
        name="Warehouse A",
        address="Address A",
        email="a@example.com",
        phone="+521111111111",
    )
    warehouse_b = Warehouse(
        name="Warehouse B",
        address="Address B",
        email="b@example.com",
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
        code="BR-FB",
        description="Producto de prueba",
        category_id=category.id,
        brand_id=brand.id,
        image=None,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    inventory_a = Inventory(
        stock=2,
        box_size=1,
        avg_cost=Decimal("10.00"),
        last_cost=Decimal("12.00"),
        warehouse_id=warehouse_a.id,
        product_id=product.id,
        is_active=True,
    )
    inventory_b = Inventory(
        stock=4,
        box_size=1,
        avg_cost=Decimal("10.00"),
        last_cost=Decimal("12.00"),
        warehouse_id=warehouse_b.id,
        product_id=product.id,
        is_active=True,
    )
    db_session.add(inventory_a)
    db_session.add(inventory_b)
    db_session.commit()
    db_session.refresh(inventory_a)
    db_session.refresh(inventory_b)

    response = client.get(
        "/api/inventory/pdf/all",
        params={"exclude_ids": str(inventory_a.id)},
    )

    assert response.status_code == 200, response.text
    assert captured["warehouse"] is not None
    assert captured["warehouse"].id == warehouse_b.id
    assert len(captured["items"]) == 1
    assert captured["items"][0].id == inventory_b.id


def test_inventory_pdf_supports_excluding_multiple_ids_with_csv(
    client, db_session, monkeypatch
):
    from src.shared.models.brand.brand_model import Brand
    from src.shared.models.category.category_model import Category
    from src.shared.models.inventory.inventory_model import Inventory
    from src.shared.models.product.product_model import Product
    from src.shared.models.warehouse.warehouse_model import Warehouse

    captured = {}

    def fake_generate_inventory_pdf(self, items, warehouse=None):
        captured["items"] = items
        return b"%PDF-1.4 excluded"

    monkeypatch.setattr(
        PDFGenerator,
        "generate_inventory_pdf",
        fake_generate_inventory_pdf,
        raising=True,
    )

    category = Category(name="Categoria Exclude CSV", description="Root")
    brand = Brand(name="Marca Exclude CSV")
    warehouse = Warehouse(
        name="Warehouse Exclude CSV",
        address="Address CSV",
        email="csv@example.com",
        phone="+521111111111",
    )
    db_session.add(category)
    db_session.add(brand)
    db_session.add(warehouse)
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(brand)
    db_session.refresh(warehouse)

    products = []
    for index in range(1, 4):
        product = Product(
            name=f"Producto CSV {index}",
            code=f"CSV-{index}",
            description="Producto de prueba",
            category_id=category.id,
            brand_id=brand.id,
            image=None,
        )
        db_session.add(product)
        products.append(product)
    db_session.commit()
    for product in products:
        db_session.refresh(product)

    inventories = []
    for index, product in enumerate(products, start=1):
        inventory = Inventory(
            stock=index,
            box_size=1,
            avg_cost=Decimal("0.00"),
            last_cost=Decimal("0.00"),
            warehouse_id=warehouse.id,
            product_id=product.id,
            is_active=True,
        )
        db_session.add(inventory)
        inventories.append(inventory)
    db_session.commit()
    for inventory in inventories:
        db_session.refresh(inventory)

    response = client.get(
        "/api/inventory/pdf/all",
        params={"exclude_ids": f"{inventories[0].id},{inventories[2].id}"},
    )

    assert response.status_code == 200, response.text
    remaining_ids = [item.id for item in captured["items"]]
    assert remaining_ids == [inventories[1].id]


def test_inventory_repository_get_report_warehouse_supports_name_and_id_filters(db_session):
    from src.shared.models.warehouse.warehouse_model import Warehouse

    warehouse_a = Warehouse(
        name="Almacen Norte Repo",
        address="Direccion Norte Repo",
        email="north.repo@example.com",
        phone="+521111111111",
    )
    warehouse_b = Warehouse(
        name="Almacen Sur Repo",
        address="Direccion Sur Repo",
        email="south.repo@example.com",
        phone="+521222222222",
    )
    db_session.add(warehouse_a)
    db_session.add(warehouse_b)
    db_session.commit()
    db_session.refresh(warehouse_a)
    db_session.refresh(warehouse_b)

    repository = InventoryRepository(db_session)

    by_name = repository.get_report_warehouse(filters={"almacen": warehouse_a.name}, items=[])
    assert by_name is not None
    assert by_name.id == warehouse_a.id

    by_id = repository.get_report_warehouse(filters={"almacen": str(warehouse_b.id)}, items=[])
    assert by_id is not None
    assert by_id.id == warehouse_b.id


def test_pdf_generator_uses_real_warehouse_header_instead_of_generic_placeholder(monkeypatch):
    generator = PDFGenerator()
    captured = {}

    def fake_render_pdf(pages_html, extra_styles=""):
        captured["pages_html"] = pages_html
        captured["extra_styles"] = extra_styles
        return b"%PDF-1.4 header"

    monkeypatch.setattr(generator, "_render_pdf", fake_render_pdf, raising=True)
    monkeypatch.setattr(
        generator,
        "_image_to_base64",
        lambda *_args, **_kwargs: "data:image/png;base64,AAA",
        raising=True,
    )

    warehouse = SimpleNamespace(
        name="Almacen Central",
        address="Av. Real 123",
        phone="+525500000000",
        email="central@example.com",
    )
    item = SimpleNamespace(
        product=SimpleNamespace(name="Bocina RINO", code="BR-10", image=None),
        stock=5,
        avg_cost=Decimal("10.00"),
        last_cost=Decimal("12.00"),
        box_size=2,
    )

    pdf_bytes = generator.generate_inventory_pdf([item], warehouse=warehouse)

    assert pdf_bytes == b"%PDF-1.4 header"
    html = captured["pages_html"]
    assert "Almacen Central" in html
    assert "Av. Real 123" in html
    assert "+525500000000" in html
    assert "central@example.com" in html
    assert "Calle Falsa 123, Ciudad" not in html
    assert "contacto@miempresa.com" not in html
    assert "Producto 01" not in html
    assert "Producto 02" not in html
    assert "Stock" not in html
    assert "AVG Cost" not in html
    assert "Last Cost" not in html
    assert "Bocina RINO" in html
    assert "Código" in html
    assert "BR-10" in html
    assert "Piezas por caja" in html
    assert "2" in html
    assert "Descripción" in html
    assert "info-row-description" in html
    assert "product-description" in html
    assert 'class="product-name"' in html
    assert 'class="image-container"' in html
    assert html.index("Bocina RINO") < html.index('class="image-container"')
    assert html.index('class="image-container"') < html.index("Código")


def test_pdf_generator_uses_nine_products_per_page(monkeypatch):
    generator = PDFGenerator()
    captured = {}

    def fake_render_pdf(pages_html, extra_styles=""):
        captured["pages_html"] = pages_html
        return b"%PDF-1.4 pages"

    monkeypatch.setattr(generator, "_render_pdf", fake_render_pdf, raising=True)
    monkeypatch.setattr(
        generator,
        "_image_to_base64",
        lambda *_args, **_kwargs: "data:image/png;base64,AAA",
        raising=True,
    )

    warehouse = SimpleNamespace(
        name="Almacen Central",
        address="Av. Real 123",
        phone="+525500000000",
        email="central@example.com",
    )
    items = [
        SimpleNamespace(
            product=SimpleNamespace(name=f"Producto {index}", code=f"COD-{index}", image=None),
            stock=index,
            avg_cost=Decimal("10.00"),
            last_cost=Decimal("12.00"),
            box_size=2,
        )
        for index in range(1, 11)
    ]

    pdf_bytes = generator.generate_inventory_pdf(items, warehouse=warehouse)

    assert pdf_bytes == b"%PDF-1.4 pages"
    html = captured["pages_html"]
    assert html.count('class="page"') == 2
    assert "Producto 10" in html


def test_inventory_pdf_returns_503_when_playwright_browser_is_missing(
    client, monkeypatch
):
    def raise_browser_missing(self, items, warehouse=None):
        raise RuntimeError(
            "Playwright browser executable is missing or unavailable. "
            "Run `playwright install chromium` in this environment."
        )

    monkeypatch.setattr(
        PDFGenerator,
        "generate_inventory_pdf",
        raise_browser_missing,
        raising=True,
    )

    response = client.get("/api/inventory/pdf/all")

    assert response.status_code == 503, response.text
    assert response.json()["message"] == "Servicio no disponible"
    assert response.json()["errors"] == []
