"""Remove product subcategory and category parent.

Revision ID: r011catsimplify
Revises: r010invcost
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r011catsimplify"
down_revision = "r010invcost"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "product" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("product")}
        if "subcategory_id" in existing_cols:
            op.drop_column("product", "subcategory_id")

    if "category" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("category")}
        if "parent_id" in existing_cols:
            op.drop_column("category", "parent_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "category" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("category")}
        if "parent_id" not in existing_cols:
            op.add_column("category", sa.Column("parent_id", sa.Integer(), nullable=True))

    if "product" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("product")}
        if "subcategory_id" not in existing_cols:
            op.add_column("product", sa.Column("subcategory_id", sa.Integer(), nullable=True))
