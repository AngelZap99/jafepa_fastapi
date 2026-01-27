from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session

from src.shared.enums.invoice_enums import InvoiceStatus
from src.shared.enums.sale_enums import SaleStatus
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.client.client_model import Client
from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.product.product_model import Product
from src.shared.models.sale.sale_model import Sale
from src.shared.models.warehouse.warehouse_model import Warehouse

from src.modules.invoice.domain.invoice_repository import InvoiceRepository
from src.modules.invoice.domain.invoice_service import InvoiceService
from src.modules.invoice.invoice_schema import InvoiceCreateWithLines, InvoiceUpdateStatus
from src.modules.invoice_line.invoice_line_schema import InvoiceLineCreate
from src.modules.sale.domain.sale_repository import SaleRepository
from src.modules.sale.domain.sale_service import SaleService
from src.modules.sale.sale_schema import SaleCreateWithLines, SaleLineCreate, SaleUpdateStatus


BUSINESS_TABLE_NAMES_TRUNCATE_ORDER: tuple[str, ...] = (
    # Parent → child order does not matter for Postgres TRUNCATE ... CASCADE,
    # but we keep an explicit list for consistency and cross-dialect deletes.
    "category",
    "brand",
    "warehouse",
    "client",
    "product",
    "invoice",
    "invoice_line",
    "inventory",
    "sale",
    "sale_line",
    "inventory_movement",
)

# Child → parent order for DELETEs in dialects without TRUNCATE ... CASCADE.
BUSINESS_TABLE_NAMES_DELETE_ORDER: tuple[str, ...] = (
    "inventory_movement",
    "sale_line",
    "invoice_line",
    "sale",
    "invoice",
    "inventory",
    "product",
    "client",
    "warehouse",
    "brand",
    "category",
)


@dataclass(frozen=True)
class SeedConfig:
    insert_mode: str  # append|skip|upsert (catalogs/products)

    categories: int
    subcategories_per_category: int
    brands: int
    warehouses: int
    clients: int

    products: int

    invoices: int
    invoice_lines: int
    arrive_invoices: bool

    sales: int
    sale_lines: int
    approve_sales: bool


def _coerce_decimal(value: str | float | int, *, places: int = 2) -> Decimal:
    q = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(q)


def _get_or_none_by(session: Session, model, **filters):
    return session.query(model).filter_by(**filters).first()


def _upsert(
    *,
    session: Session,
    model,
    unique_filters: dict,
    create_kwargs: dict,
    update_kwargs: dict,
    insert_mode: str,
):
    existing = _get_or_none_by(session, model, **unique_filters)
    if existing and insert_mode == "skip":
        return existing, False
    if existing and insert_mode == "upsert":
        for k, v in update_kwargs.items():
            setattr(existing, k, v)
        session.add(existing)
        return existing, True
    if existing and insert_mode == "append":
        # let the caller handle potential uniqueness conflicts elsewhere
        pass

    obj = model(**create_kwargs)
    session.add(obj)
    return obj, True


def seed_catalogs(*, session: Session, rng: random.Random, config: SeedConfig) -> None:
    insert_mode = config.insert_mode

    existing_roots = (
        session.query(Category).filter(Category.parent_id == None).count()  # noqa: E711
    )

    # Categories (roots)
    root_categories: list[Category] = []
    for i in range(1, config.categories + 1):
        idx = existing_roots + i
        name = f"Category {idx}"
        obj, _ = _upsert(
            session=session,
            model=Category,
            unique_filters={"name": name, "parent_id": None},
            create_kwargs={
                "name": name,
                "description": f"Root category {idx}",
                "parent_id": None,
            },
            update_kwargs={"description": f"Root category {idx}", "is_active": True},
            insert_mode=insert_mode,
        )
        root_categories.append(obj)

    session.commit()
    for c in root_categories:
        session.refresh(c)

    # Subcategories (same table; parent_id points to root category)
    for parent in root_categories:
        for j in range(1, config.subcategories_per_category + 1):
            name = f"{parent.name} / Sub {j}"
            _upsert(
                session=session,
                model=Category,
                unique_filters={"name": name, "parent_id": parent.id},
                create_kwargs={
                    "name": name,
                    "description": f"Subcategory {j} of {parent.name}",
                    "parent_id": parent.id,
                },
                update_kwargs={"description": f"Subcategory {j} of {parent.name}", "is_active": True},
                insert_mode=insert_mode,
            )

    # Brands
    existing_brands = session.query(Brand).count()
    for i in range(1, config.brands + 1):
        idx = existing_brands + i
        name = f"Brand {idx}"
        _upsert(
            session=session,
            model=Brand,
            unique_filters={"name": name},
            create_kwargs={"name": name},
            update_kwargs={"name": name, "is_active": True},
            insert_mode=insert_mode,
        )

    # Warehouses
    existing_warehouses = session.query(Warehouse).count()
    for i in range(1, config.warehouses + 1):
        idx = existing_warehouses + i
        name = f"Warehouse {idx}"
        address = f"Address {idx}"
        _upsert(
            session=session,
            model=Warehouse,
            unique_filters={"name": name, "address": address},
            create_kwargs={"name": name, "address": address},
            update_kwargs={"address": address, "is_active": True},
            insert_mode=insert_mode,
        )

    # Clients
    # Keep email unique for re-runs without reset
    existing_clients = session.query(Client).count()
    for i in range(1, config.clients + 1):
        idx = existing_clients + i
        email = f"client{idx}@example.com"
        name = f"Client {idx}"
        phone = f"+52{rng.randint(1000000000, 9999999999)}"
        _upsert(
            session=session,
            model=Client,
            unique_filters={"email": email},
            create_kwargs={"name": name, "email": email, "phone": phone},
            update_kwargs={"name": name, "phone": phone, "is_active": True},
            insert_mode=insert_mode,
        )

    session.commit()


def seed_products(*, session: Session, rng: random.Random, config: SeedConfig) -> None:
    insert_mode = config.insert_mode

    roots = session.query(Category).filter(Category.parent_id == None).all()  # noqa: E711
    subs = session.query(Category).filter(Category.parent_id != None).all()  # noqa: E711
    brands = session.query(Brand).all()
    if not roots or not brands:
        raise RuntimeError("Missing catalogs: seed catalogs before products.")

    existing_products = session.query(Product).count()
    for i in range(1, config.products + 1):
        idx = existing_products + i
        code = f"SKU{idx:05d}"
        name = f"Product {idx}"
        category = rng.choice(roots)
        subcategory = rng.choice(subs) if subs and rng.random() < 0.7 else None
        brand = rng.choice(brands)

        _upsert(
            session=session,
            model=Product,
            unique_filters={"code": code},
            create_kwargs={
                "name": name,
                "code": code,
                "description": f"Seeded product {idx}",
                "category_id": category.id,
                "subcategory_id": subcategory.id if subcategory else None,
                "brand_id": brand.id,
                "image": None,
                "is_active": True,
            },
            update_kwargs={
                "name": name,
                "description": f"Seeded product {idx}",
                "category_id": category.id,
                "subcategory_id": subcategory.id if subcategory else None,
                "brand_id": brand.id,
                "image": None,
                "is_active": True,
            },
            insert_mode=insert_mode,
        )

    session.commit()


def seed_invoices(*, session: Session, rng: random.Random, config: SeedConfig) -> None:
    products = session.query(Product).filter(Product.is_active == True).all()  # noqa: E712
    warehouses = session.query(Warehouse).filter(Warehouse.is_active == True).all()  # noqa: E712
    if not products or not warehouses:
        raise RuntimeError("Missing products/warehouses: seed catalogs + products first.")

    invoice_repo = InvoiceRepository(session)
    invoice_service = InvoiceService(invoice_repo)

    # Continue sequences for re-runs without reset
    max_sequence = session.query(Invoice.sequence).order_by(Invoice.sequence.desc()).first()
    next_sequence = (max_sequence[0] if max_sequence else 0) + 1

    box_sizes = [1, 6, 12, 24]
    for inv_i in range(config.invoices):
        warehouse = rng.choice(warehouses)
        invoice_number = "INV"
        sequence = next_sequence + inv_i

        inv_date = date.today() - timedelta(days=rng.randint(0, 30))
        order_date = inv_date
        arrival_date = inv_date + timedelta(days=rng.randint(0, 3))

        # Build lines with unique (product_id, box_size)
        rng.shuffle(products)
        chosen_products = products[: min(len(products), max(0, config.invoice_lines))]
        lines: list[InvoiceLineCreate] = []
        seen_keys: set[tuple[int, int]] = set()
        for p in chosen_products:
            box = rng.choice(box_sizes)
            key = (p.id, box)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            quantity_boxes = rng.randint(1, 15)
            price = _coerce_decimal(rng.uniform(5, 150), places=2)
            lines.append(
                InvoiceLineCreate(
                    product_id=p.id,
                    box_size=box,
                    quantity_boxes=quantity_boxes,
                    price=price,
                )
            )

        payload = InvoiceCreateWithLines(
            invoice_number=invoice_number,
            sequence=sequence,
            invoice_date=inv_date,
            order_date=order_date,
            arrival_date=arrival_date,
            status=InvoiceStatus.DRAFT,
            dollar_exchange_rate=_coerce_decimal(rng.uniform(1.0, 20.0), places=6),
            logistic_tax=_coerce_decimal(rng.uniform(0, 500), places=2),
            notes=f"Seeded invoice {sequence}",
            warehouse_id=warehouse.id,
            lines=lines,
        )

        invoice = invoice_service.create_invoice(payload)

        if config.arrive_invoices:
            invoice_service.update_invoice_status(
                invoice.id,
                InvoiceUpdateStatus(status=InvoiceStatus.ARRIVED),
            )


def seed_sales(*, session: Session, rng: random.Random, config: SeedConfig) -> None:
    clients = session.query(Client).filter(Client.is_active == True).all()  # noqa: E712
    if not clients:
        raise RuntimeError("Missing clients: seed catalogs first.")

    sale_repo = SaleRepository(session)
    sale_service = SaleService(sale_repo)

    # Use live inventory so approval doesn't fail later.
    for _ in range(config.sales):
        inventories = (
            session.query(Inventory)
            .filter(Inventory.is_active == True, Inventory.stock > 0)  # noqa: E712
            .all()
        )
        if not inventories:
            break

        client = rng.choice(clients)
        rng.shuffle(inventories)
        picked = inventories[: min(len(inventories), max(0, config.sale_lines))]

        lines: list[SaleLineCreate] = []
        for inv in picked:
            # Keep quantities small to reduce collisions across many sales
            qty = rng.randint(1, min(5, inv.stock))
            price = _coerce_decimal(rng.uniform(5, 150), places=2)
            lines.append(
                SaleLineCreate(
                    inventory_id=inv.id,
                    quantity_units=qty,
                    price=price,
                )
            )

        if not lines:
            continue

        payload = SaleCreateWithLines(
            sale_date=date.today() - timedelta(days=rng.randint(0, 30)),
            status=SaleStatus.DRAFT,
            notes="Seeded sale",
            client_id=client.id,
            lines=lines,
        )

        try:
            sale = sale_service.create_sale(payload)
        except HTTPException:
            # Stock might have changed; skip this sale
            continue

        if config.approve_sales:
            try:
                sale_service.update_sale_status(
                    sale.id, SaleUpdateStatus(status=SaleStatus.APPROVED)
                )
            except HTTPException:
                # If approval fails (stock contention), keep it as DRAFT
                pass


def seed_summary(*, session: Session) -> str:
    def count(model) -> int:
        return session.query(model).count()

    parts = [
        f"Seed complete:",
        f"- categories: {count(Category)}",
        f"- brands: {count(Brand)}",
        f"- warehouses: {count(Warehouse)}",
        f"- clients: {count(Client)}",
        f"- products: {count(Product)}",
        f"- invoices: {count(Invoice)}",
        f"- inventory: {count(Inventory)}",
        f"- sales: {count(Sale)}",
    ]
    return "\n".join(parts)
