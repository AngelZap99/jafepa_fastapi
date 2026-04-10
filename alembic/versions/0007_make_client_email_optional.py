"""Make client email optional.

Revision ID: r007clnt
Revises: r006invline
Create Date: 2026-04-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r007clnt"
down_revision = "r006invline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "client" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("client")}
    if "email" in existing_cols:
        op.alter_column(
            "client",
            "email",
            existing_type=sa.String(length=50),
            nullable=True,
        )


def downgrade() -> None:
    # Downgrade intentionally omitted to avoid breaking clients with null emails.
    pass
