"""Convert inventory costs to decimal.

Revision ID: r010invcost
Revises: r009invprofit
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r010invcost"
down_revision = "r009invprofit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "inventory" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("inventory")}
    numeric_type = sa.Numeric(12, 6)

    if "avg_cost" in existing_cols:
        alter_kwargs = {
            "existing_nullable": False,
            "type_": numeric_type,
        }
        if bind.dialect.name == "postgresql":
            alter_kwargs["postgresql_using"] = "avg_cost::numeric(12,6)"
        op.alter_column("inventory", "avg_cost", **alter_kwargs)

    if "last_cost" in existing_cols:
        alter_kwargs = {
            "existing_nullable": False,
            "type_": numeric_type,
        }
        if bind.dialect.name == "postgresql":
            alter_kwargs["postgresql_using"] = "last_cost::numeric(12,6)"
        op.alter_column("inventory", "last_cost", **alter_kwargs)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "inventory" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("inventory")}
    float_type = sa.Float()

    if "avg_cost" in existing_cols:
        alter_kwargs = {
            "existing_nullable": False,
            "type_": float_type,
        }
        if bind.dialect.name == "postgresql":
            alter_kwargs["postgresql_using"] = "avg_cost::double precision"
        op.alter_column("inventory", "avg_cost", **alter_kwargs)

    if "last_cost" in existing_cols:
        alter_kwargs = {
            "existing_nullable": False,
            "type_": float_type,
        }
        if bind.dialect.name == "postgresql":
            alter_kwargs["postgresql_using"] = "last_cost::double precision"
        op.alter_column("inventory", "last_cost", **alter_kwargs)
