"""Add invoice approximate profit rate.

Revision ID: r009invprofit
Revises: r008sale
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r009invprofit"
down_revision = "r008sale"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "invoice" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("invoice")}

    if "approximate_profit_rate" not in existing_cols:
        op.add_column(
            "invoice",
            sa.Column(
                "approximate_profit_rate",
                sa.Numeric(12, 2),
                nullable=False,
                server_default="0.00",
            ),
        )
        op.alter_column("invoice", "approximate_profit_rate", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "invoice" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("invoice")}
    if "approximate_profit_rate" in existing_cols:
        op.drop_column("invoice", "approximate_profit_rate")
