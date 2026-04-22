"""Add missing inventory movement event enum values for sales.

Revision ID: r016saleeventenum
Revises: r015salesreserve
Create Date: 2026-04-21
"""

from alembic import op
from sqlalchemy import text


revision = "r016saleeventenum"
down_revision = "r015salesreserve"
branch_labels = None
depends_on = None


def _add_enum_value(enum_name: str, value: str) -> None:
    op.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))


def upgrade() -> None:
    _add_enum_value("inventoryeventtype", "SALE_RESERVED")
    _add_enum_value("inventoryeventtype", "SALE_RELEASED")
    _add_enum_value("inventoryeventtype", "SALE_APPROVED")
    _add_enum_value("inventoryeventtype", "SALE_REVERSED")
    _add_enum_value("inventoryeventtype", "BOX_OPENED_OUT")
    _add_enum_value("inventoryeventtype", "BOX_OPENED_IN")


def downgrade() -> None:
    # PostgreSQL enums cannot safely drop individual values in place.
    pass
