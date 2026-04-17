"""Rename inventory movement value field and align UTC-aware timestamps.

Revision ID: r013invmovutc
Revises: r012invmovvalue
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r013invmovutc"
down_revision = "r012invmovvalue"
branch_labels = None
depends_on = None


def _alter_timestamp_to_timezone(
    table_name: str,
    column_name: str,
    *,
    dialect: str,
    existing_nullable: bool,
) -> None:
    if dialect == "postgresql":
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name}
                ALTER COLUMN {column_name}
                TYPE TIMESTAMP WITH TIME ZONE
                USING {column_name} AT TIME ZONE 'UTC'
                """
            )
        )
        return

    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=existing_nullable,
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    table_names = inspector.get_table_names()
    if "inventory_movement" not in table_names:
        return

    movement_columns = {
        column["name"]: column for column in inspector.get_columns("inventory_movement")
    }

    if "unit_cost" in movement_columns and "unit_value" not in movement_columns:
        with op.batch_alter_table("inventory_movement") as batch_op:
            batch_op.alter_column(
                "unit_cost",
                new_column_name="unit_value",
                existing_type=sa.Numeric(12, 6),
                existing_nullable=False,
            )

    op.execute(
        """
        UPDATE inventory_movement
        SET is_active = TRUE
        WHERE source_type = 'INVOICE'
          AND event_type = 'INVOICE_RECEIVED'
          AND movement_type = 'IN_'
          AND is_active = FALSE
        """
    )

    _alter_timestamp_to_timezone(
        "inventory_movement",
        "movement_date",
        dialect=dialect,
        existing_nullable=False,
    )

    for table_name in table_names:
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "deleted_at" in columns:
            _alter_timestamp_to_timezone(
                table_name,
                "deleted_at",
                dialect=dialect,
                existing_nullable=True,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    table_names = inspector.get_table_names()
    if "inventory_movement" not in table_names:
        return

    movement_columns = {
        column["name"]: column for column in inspector.get_columns("inventory_movement")
    }

    if "unit_value" in movement_columns and "unit_cost" not in movement_columns:
        with op.batch_alter_table("inventory_movement") as batch_op:
            batch_op.alter_column(
                "unit_value",
                new_column_name="unit_cost",
                existing_type=sa.Numeric(12, 6),
                existing_nullable=False,
            )

    if dialect == "postgresql":
        op.execute(
            """
            UPDATE inventory_movement
            SET is_active = FALSE
            WHERE source_type = 'INVOICE'
              AND event_type = 'INVOICE_RECEIVED'
              AND movement_type = 'IN_'
              AND invoice_line_id IN (
                  SELECT invoice_line_id
                  FROM inventory_movement
                  WHERE source_type = 'INVOICE'
                    AND event_type = 'INVOICE_UNRECEIVED'
                    AND invoice_line_id IS NOT NULL
              )
            """
        )

    for table_name in table_names:
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "deleted_at" in columns and dialect == "postgresql":
            op.execute(
                sa.text(
                    f"""
                    ALTER TABLE {table_name}
                    ALTER COLUMN deleted_at
                    TYPE TIMESTAMP WITHOUT TIME ZONE
                    USING deleted_at AT TIME ZONE 'UTC'
                    """
                )
            )

    if dialect == "postgresql":
        op.execute(
            """
            ALTER TABLE inventory_movement
            ALTER COLUMN movement_date
            TYPE TIMESTAMP WITHOUT TIME ZONE
            USING movement_date AT TIME ZONE 'UTC'
            """
        )
