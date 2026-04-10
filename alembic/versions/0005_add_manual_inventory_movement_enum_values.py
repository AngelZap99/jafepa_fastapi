"""Add manual inventory movement enum values.

Revision ID: r005inv
Revises: 0004_add_user_role
Create Date: 2026-04-10
"""

from alembic import op
from sqlalchemy import text


revision = "r005inv"
down_revision = "0004_add_user_role"
branch_labels = None
depends_on = None


def _add_enum_value(enum_name: str, value: str) -> None:
    op.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))


def upgrade() -> None:
    # PostgreSQL enum extension for the new manual inventory history events.
    _add_enum_value("inventoryeventtype", "MANUAL_CREATED")
    _add_enum_value("inventoryeventtype", "MANUAL_STOCK_ADJUSTED")

    # Keep source_type aligned with the model in case the DB predates MANUAL.
    _add_enum_value("inventorysourcetype", "MANUAL")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely in place.
    # Downgrade is intentionally a no-op.
    pass
