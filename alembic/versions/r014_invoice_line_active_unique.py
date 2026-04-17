"""Enforce unique active invoice lines by invoice, product and box size.

Revision ID: r014invlineuniq
Revises: r013invmovutc
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r014invlineuniq"
down_revision = "r013invmovutc"
branch_labels = None
depends_on = None


INDEX_NAME = "uq_invoice_line_active_keys"


def _index_exists(bind) -> bool:
    inspector = inspect(bind)
    return any(
        index["name"] == INDEX_NAME for index in inspector.get_indexes("invoice_line")
    )


def _assert_no_active_duplicates(bind, *, dialect: str) -> None:
    active_flag = "TRUE" if dialect == "postgresql" else "1"
    rows = bind.execute(
        sa.text(
            f"""
            SELECT invoice_id, product_id, box_size, COUNT(*) AS total
            FROM invoice_line
            WHERE is_active = {active_flag}
            GROUP BY invoice_id, product_id, box_size
            HAVING COUNT(*) > 1
            ORDER BY invoice_id, product_id, box_size
            LIMIT 10
            """
        )
    ).fetchall()

    if not rows:
        return

    duplicates = ", ".join(
        f"(invoice_id={row.invoice_id}, product_id={row.product_id}, box_size={row.box_size}, total={row.total})"
        for row in rows
    )
    raise RuntimeError(
        "No se puede crear el índice único de líneas activas de factura porque "
        f"ya existen duplicados: {duplicates}"
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    if "invoice_line" not in inspector.get_table_names() or _index_exists(bind):
        return

    _assert_no_active_duplicates(bind, dialect=dialect)

    if dialect == "postgresql":
        op.create_index(
            INDEX_NAME,
            "invoice_line",
            ["invoice_id", "product_id", "box_size"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
        )
        return

    if dialect == "sqlite":
        op.create_index(
            INDEX_NAME,
            "invoice_line",
            ["invoice_id", "product_id", "box_size"],
            unique=True,
            sqlite_where=sa.text("is_active = 1"),
        )
        return

    op.create_index(
        INDEX_NAME,
        "invoice_line",
        ["invoice_id", "product_id", "box_size"],
        unique=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "invoice_line" not in inspector.get_table_names() or not _index_exists(bind):
        return

    op.drop_index(INDEX_NAME, table_name="invoice_line")
