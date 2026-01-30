"""Create tables (idempotent via SQLModel.create_all).

Revision ID: 0002_create_tables_sqlmodel
Revises: 0001_baseline
Create Date: 2026-01-30
"""

from alembic import op
from sqlmodel import SQLModel, text

import src.shared.models.register_models  # noqa: F401


revision = "0002_create_tables_sqlmodel"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        bind.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    SQLModel.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Non-destructive: we don't drop tables automatically.
    pass

