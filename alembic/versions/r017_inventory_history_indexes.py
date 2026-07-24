"""Add indexes for inventory movement history filters.

Revision ID: r017invmovindexes
Revises: r016saleeventenum
Create Date: 2026-06-23
"""

from alembic import context, op
from sqlalchemy import inspect


revision = "r017invmovindexes"
down_revision = "r016saleeventenum"
branch_labels = None
depends_on = None


INDEXES = (
    (
        "inventory_movement",
        "ix_inventory_movement_active_date_id",
        ["is_active", "movement_date", "id"],
    ),
    (
        "inventory_movement",
        "ix_inventory_movement_inventory_date_id",
        ["inventory_id", "movement_date", "id"],
    ),
    (
        "inventory_movement",
        "ix_inventory_movement_created_by_date_id",
        ["created_by", "movement_date", "id"],
    ),
    (
        "inventory_movement",
        "ix_inventory_movement_source_movement_date",
        ["source_type", "movement_type", "movement_date"],
    ),
    (
        "inventory_movement",
        "ix_inventory_movement_movement_type",
        ["movement_type"],
    ),
    (
        "inventory",
        "ix_inventory_product_warehouse",
        ["product_id", "warehouse_id"],
    ),
    ("invoice", "ix_invoice_created_by", ["created_by"]),
    ("invoice", "ix_invoice_updated_by", ["updated_by"]),
    ("sale", "ix_sale_created_by", ["created_by"]),
    ("sale", "ix_sale_updated_by", ["updated_by"]),
    ("sale", "ix_sale_paid_by", ["paid_by"]),
    ("sale", "ix_sale_cancelled_by", ["cancelled_by"]),
)


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if context.is_offline_mode():
        for table_name, index_name, columns in INDEXES:
            op.create_index(index_name, table_name, columns, unique=False)
        return

    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    for table_name, index_name, columns in INDEXES:
        if table_name not in table_names:
            continue
        if _index_exists(inspector, table_name, index_name):
            continue
        op.create_index(index_name, table_name, columns, unique=False)


def downgrade() -> None:
    if context.is_offline_mode():
        for table_name, index_name, _columns in reversed(INDEXES):
            op.drop_index(index_name, table_name=table_name)
        return

    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    for table_name, index_name, _columns in reversed(INDEXES):
        if table_name not in table_names:
            continue
        if _index_exists(inspector, table_name, index_name):
            op.drop_index(index_name, table_name=table_name)
