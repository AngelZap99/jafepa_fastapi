"""Add warehouse.email and warehouse.phone (safe if already present).

Revision ID: 0003_add_warehouse_email_phone
Revises: 0002_create_tables_sqlmodel
Create Date: 2026-01-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0003_add_warehouse_email_phone"
down_revision = "0002_create_tables_sqlmodel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "warehouse" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("warehouse")}

    if "email" not in existing_cols:
        op.add_column("warehouse", sa.Column("email", sa.String(length=50), nullable=True))

    if "phone" not in existing_cols:
        op.add_column("warehouse", sa.Column("phone", sa.String(length=25), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "warehouse" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("warehouse")}

    if "email" in existing_cols:
        op.drop_column("warehouse", "email")

    if "phone" in existing_cols:
        op.drop_column("warehouse", "phone")

