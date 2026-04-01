"""Add users.role with backfill for existing records.

Revision ID: 0004_add_user_role
Revises: 0003_add_warehouse_email_phone
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_add_user_role"
down_revision = "0003_add_warehouse_email_phone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "users" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("users")}

    if "role" not in existing_cols:
        op.add_column(
            "users",
            sa.Column(
                "role",
                sa.String(length=20),
                nullable=False,
                server_default="Vendedor",
            ),
        )

    bind.execute(
        sa.text(
            """
            UPDATE users
            SET role = CASE
                WHEN is_admin = true THEN 'Administrador'
                ELSE 'Vendedor'
            END
            WHERE role IS NULL OR role = ''
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE users
            SET role = 'Administrador'
            WHERE is_admin = true
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE users
            SET role = 'Vendedor'
            WHERE role NOT IN ('Administrador', 'Vendedor', 'Almacenista', 'Mixto')
            """
        )
    )

    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "users" not in inspector.get_table_names():
        return

    existing_cols = {c["name"] for c in inspector.get_columns("users")}
    if "role" in existing_cols:
        op.drop_column("users", "role")
