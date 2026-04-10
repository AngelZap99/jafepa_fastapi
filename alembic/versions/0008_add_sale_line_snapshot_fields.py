"""Add sale line snapshot fields.

Revision ID: r008sale
Revises: r007clnt
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r008sale"
down_revision = "r007clnt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "sale_line" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("sale_line")}
    price_type_enum = sa.Enum("UNIT", "BOX", name="salelinepricetype")
    price_type_enum.create(bind, checkfirst=True)

    if "box_size" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column("box_size", sa.Integer(), nullable=False, server_default="1"),
        )
        op.alter_column("sale_line", "box_size", server_default=None)

    if "price_type" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column(
                "price_type",
                price_type_enum,
                nullable=False,
                server_default="BOX",
            ),
        )
        op.alter_column("sale_line", "price_type", server_default=None)

    if "unit_price" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column(
                "unit_price",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
        op.alter_column("sale_line", "unit_price", server_default=None)

    if "box_price" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column(
                "box_price",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
        op.alter_column("sale_line", "box_price", server_default=None)

    if "product_code" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column("product_code", sa.String(length=100), nullable=True),
        )

    if "product_name" not in existing_cols:
        op.add_column(
            "sale_line",
            sa.Column("product_name", sa.String(length=250), nullable=True),
        )

    # Backfill historical rows for readability and reporting.
    op.execute(
        sa.text(
            """
            UPDATE sale_line AS sl
            SET
                box_size = COALESCE(inv.box_size, 1),
                price_type = 'BOX',
                unit_price = CASE
                    WHEN COALESCE(inv.box_size, 1) > 0
                        THEN ROUND(sl.price / COALESCE(inv.box_size, 1), 2)
                    ELSE sl.price
                END,
                box_price = sl.price,
                product_code = prod.code,
                product_name = prod.name
            FROM inventory AS inv
            JOIN product AS prod ON prod.id = inv.product_id
            WHERE sl.inventory_id = inv.id
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "sale_line" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("sale_line")}
    if "product_name" in existing_cols:
        op.drop_column("sale_line", "product_name")
    if "product_code" in existing_cols:
        op.drop_column("sale_line", "product_code")
    if "box_price" in existing_cols:
        op.drop_column("sale_line", "box_price")
    if "unit_price" in existing_cols:
        op.drop_column("sale_line", "unit_price")
    if "price_type" in existing_cols:
        op.drop_column("sale_line", "price_type")
    if "box_size" in existing_cols:
        op.drop_column("sale_line", "box_size")

    price_type_enum = sa.Enum("UNIT", "BOX", name="salelinepricetype")
    price_type_enum.drop(bind, checkfirst=True)
