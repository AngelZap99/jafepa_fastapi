"""Add invoice line price type.

Revision ID: r006invline
Revises: r005inv
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r006invline"
down_revision = "r005inv"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "invoice_line" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("invoice_line")}
    price_type_enum = sa.Enum("UNIT", "BOX", name="invoicelinepricetype")
    price_type_enum.create(bind, checkfirst=True)

    if "price_type" not in existing_cols:
        op.add_column(
            "invoice_line",
            sa.Column(
                "price_type",
                price_type_enum,
                nullable=False,
                server_default="BOX",
            ),
        )
        op.alter_column("invoice_line", "price_type", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "invoice_line" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("invoice_line")}
    if "price_type" in existing_cols:
        op.drop_column("invoice_line", "price_type")

    price_type_enum = sa.Enum("UNIT", "BOX", name="invoicelinepricetype")
    price_type_enum.drop(bind, checkfirst=True)
