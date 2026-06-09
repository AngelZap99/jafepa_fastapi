"""Add value type to inventory movements.

Revision ID: r012invmovvalue
Revises: r011catsimplify
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r012invmovvalue"
down_revision = "r011catsimplify"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    value_type_enum = sa.Enum("COST", "PRICE", name="inventoryvaluetype")

    if "inventory_movement" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]: column for column in inspector.get_columns("inventory_movement")
    }
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("inventory_movement")
    }

    if "value_type" not in existing_columns:
        op.add_column(
            "inventory_movement",
            sa.Column("value_type", value_type_enum, nullable=True),
        )
        value_type_column_type = value_type_enum
    else:
        value_type_column_type = existing_columns["value_type"]["type"]

    is_postgres_enum = bind.dialect.name == "postgresql" and isinstance(
        value_type_column_type, sa.Enum
    )

    if is_postgres_enum:
        op.execute(
            """
            UPDATE inventory_movement
            SET value_type = CASE
                WHEN source_type = 'SALE' THEN 'PRICE'::inventoryvaluetype
                ELSE 'COST'::inventoryvaluetype
            END
            WHERE value_type IS NULL
            """
        )
    else:
        op.execute(
            """
            UPDATE inventory_movement
            SET value_type = CASE
                WHEN source_type = 'SALE' THEN 'PRICE'
                ELSE 'COST'
            END
            WHERE value_type IS NULL
            """
        )

    op.alter_column(
        "inventory_movement",
        "value_type",
        nullable=False,
    )

    if "ix_inventory_movement_value_type" not in existing_indexes:
        op.create_index(
            "ix_inventory_movement_value_type",
            "inventory_movement",
            ["value_type"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "inventory_movement" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("inventory_movement")}
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("inventory_movement")}

    if "ix_inventory_movement_value_type" in existing_indexes:
        op.drop_index("ix_inventory_movement_value_type", table_name="inventory_movement")

    if "value_type" in existing_cols:
        op.drop_column("inventory_movement", "value_type")
