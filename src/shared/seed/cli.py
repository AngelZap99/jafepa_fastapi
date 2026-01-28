from __future__ import annotations

import random
from enum import Enum
from typing import List

import typer

from sqlmodel import Session, SQLModel, text

# Ensure all SQLModel tables are registered in metadata
import src.shared.models.register_models  # noqa: F401

from src.shared.seed.seeder import (
    BUSINESS_TABLE_NAMES_DELETE_ORDER,
    BUSINESS_TABLE_NAMES_TRUNCATE_ORDER,
    SeedConfig,
    seed_catalogs,
    seed_invoices,
    seed_products,
    seed_sales,
    seed_summary,
)


app = typer.Typer(add_completion=False, help="JAFEPA database seeder (dev tool).")


class Phase(str, Enum):
    catalogs = "catalogs"
    products = "products"
    invoices = "invoices"
    sales = "sales"


class InsertMode(str, Enum):
    append = "append"
    skip = "skip"
    upsert = "upsert"


def _get_engine():
    from src.shared.database.database_config import engine

    return engine


def _reset_db(*, yes: bool) -> None:
    if not yes:
        typer.echo(
            "Refusing to reset without --yes (this resets BUSINESS tables only; users are kept)."
        )
        raise typer.Exit(code=2)

    # Mirror `main.py` startup extension creation
    import os

    db_dialect = os.getenv("DB_DIALECT", "")
    engine = _get_engine()

    # Ensure schema exists. This may create missing tables (including `users`),
    # but we never TRUNCATE/DELETE the `users` table.
    SQLModel.metadata.create_all(engine)

    if db_dialect.lower() == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
            tables_sql = ", ".join(f"\"{name}\"" for name in BUSINESS_TABLE_NAMES_TRUNCATE_ORDER)
            conn.execute(text(f"TRUNCATE TABLE {tables_sql} RESTART IDENTITY CASCADE;"))
        return

    # Fallback for non-Postgres dialects
    with Session(engine) as session:
        for table_name in BUSINESS_TABLE_NAMES_DELETE_ORDER:
            table = SQLModel.metadata.tables.get(table_name)
            if table is None:
                continue
            session.execute(table.delete())
        session.commit()


@app.command("migrate-sales-approved-to-paid")
def migrate_sales_approved_to_paid(
    yes: bool = typer.Option(False, help="Confirm running the data migration."),
) -> None:
    """
    One-time data migration:
    - sale.status: APPROVED -> PAID

    This keeps the codebase compatible after removing APPROVED from SaleStatus.
    """
    if not yes:
        typer.echo("Refusing to migrate without --yes.")
        raise typer.Exit(code=2)

    engine = _get_engine()
    # If Postgres enum is used for the column, ensure PAID exists as a label.
    # Postgres requires new enum values to be COMMITTED before being used, so the
    # ALTER TYPE must run in a separate autocommit context (or separate TX).
    try:
        with engine.connect() as conn:
            udt_name = conn.execute(
                text(
                    "SELECT udt_name FROM information_schema.columns "
                    "WHERE table_name = 'sale' AND column_name = 'status' "
                    "LIMIT 1;"
                )
            ).scalar()

        if udt_name:
            udt_name = str(udt_name)
            if udt_name not in {"varchar", "text"} and not udt_name.startswith("_"):
                with engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as conn:
                    conn.execute(
                        text(f"ALTER TYPE \"{udt_name}\" ADD VALUE IF NOT EXISTS 'PAID';")
                    )
    except Exception:
        # Best-effort: if this fails, the UPDATE below might still work (e.g., varchar status).
        pass

    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE sale SET status = 'PAID' WHERE status = 'APPROVED';")
        )
        typer.echo(f"Migrated {result.rowcount or 0} sale rows: APPROVED -> PAID")


@app.callback(invoke_without_command=True)
def seed(
    ctx: typer.Context,
    phases: List[Phase] = typer.Option(
        default=[Phase.catalogs, Phase.products, Phase.invoices, Phase.sales],
        help="Phases to run (repeatable). Order matters.",
    ),
    reset: bool = typer.Option(
        False,
        help="Reset BUSINESS tables only (keeps users) before seeding.",
    ),
    yes: bool = typer.Option(False, help="Confirm destructive actions like --reset."),
    insert_mode: InsertMode = typer.Option(
        InsertMode.skip,
        help="How to behave when a record already exists (catalogs/products).",
    ),
    seed_value: int = typer.Option(123, help="Deterministic RNG seed."),
    # ---- catalogs
    categories: int = typer.Option(6, min=0),
    subcategories_per_category: int = typer.Option(3, min=0),
    brands: int = typer.Option(8, min=0),
    warehouses: int = typer.Option(2, min=0),
    clients: int = typer.Option(20, min=0),
    # ---- products
    products: int = typer.Option(60, min=0),
    # ---- invoices (inbound stock)
    invoices: int = typer.Option(15, min=0),
    invoice_lines: int = typer.Option(6, min=0, help="Lines per invoice (max)."),
    arrive_invoices: bool = typer.Option(
        True, help="Transition invoices to ARRIVED to apply inventory movements."
    ),
    # ---- sales (outbound stock)
    sales: int = typer.Option(25, min=0),
    sale_lines: int = typer.Option(4, min=0, help="Lines per sale (max)."),
    pay_sales: bool = typer.Option(
        True,
        "--pay-sales/--no-pay-sales",
        "--approve-sales/--no-approve-sales",
        help="Transition sales to PAID to apply inventory movements.",
    ),
) -> None:
    """
    Seeds the database with coherent demo data:
    catalogs → products → invoices (stock IN) → sales (stock OUT).
    """
    if ctx.invoked_subcommand is not None:
        return

    if reset:
        _reset_db(yes=yes)

    engine = _get_engine()
    # Keep behavior consistent with app startup: auto-create tables if missing.
    SQLModel.metadata.create_all(engine)

    rng = random.Random(seed_value)
    config = SeedConfig(
        insert_mode=insert_mode.value,
        categories=categories,
        subcategories_per_category=subcategories_per_category,
        brands=brands,
        warehouses=warehouses,
        clients=clients,
        products=products,
        invoices=invoices,
        invoice_lines=invoice_lines,
        arrive_invoices=arrive_invoices,
        sales=sales,
        sale_lines=sale_lines,
        pay_sales=pay_sales,
    )

    with Session(engine) as session:
        for phase in phases:
            if phase == Phase.catalogs:
                seed_catalogs(session=session, rng=rng, config=config)
            elif phase == Phase.products:
                seed_products(session=session, rng=rng, config=config)
            elif phase == Phase.invoices:
                seed_invoices(session=session, rng=rng, config=config)
            elif phase == Phase.sales:
                seed_sales(session=session, rng=rng, config=config)

        summary = seed_summary(session=session)
        typer.echo(summary)
