"""Add sale audit fields and reservation support.

Revision ID: r015salesreserve
Revises: r014invlineuniq
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "r015salesreserve"
down_revision = "r014invlineuniq"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_fk(inspector, table_name: str, fk_name: str) -> bool:
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = inspector.get_table_names()

    if "inventory" in table_names and not _has_column(inspector, "inventory", "reserved_stock"):
        with op.batch_alter_table("inventory") as batch_op:
            batch_op.add_column(
                sa.Column("reserved_stock", sa.Integer(), nullable=False, server_default="0")
            )

    if "sale" in table_names:
        with op.batch_alter_table("sale") as batch_op:
            if not _has_column(inspector, "sale", "paid_by"):
                batch_op.add_column(sa.Column("paid_by", sa.Integer(), nullable=True))
            if not _has_column(inspector, "sale", "cancelled_by"):
                batch_op.add_column(sa.Column("cancelled_by", sa.Integer(), nullable=True))
            if not _has_column(inspector, "sale", "paid_at"):
                batch_op.add_column(
                    sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True)
                )
            if not _has_column(inspector, "sale", "cancelled_at"):
                batch_op.add_column(
                    sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True)
                )

        inspector = inspect(bind)
        if not _has_fk(inspector, "sale", "fk_sale_paid_by_user"):
            op.create_foreign_key(
                "fk_sale_paid_by_user", "sale", "users", ["paid_by"], ["id"]
            )
        if not _has_fk(inspector, "sale", "fk_sale_cancelled_by_user"):
            op.create_foreign_key(
                "fk_sale_cancelled_by_user",
                "sale",
                "users",
                ["cancelled_by"],
                ["id"],
            )

    if "sale_line" in table_names:
        with op.batch_alter_table("sale_line") as batch_op:
            if not _has_column(inspector, "sale_line", "reservation_applied"):
                batch_op.add_column(
                    sa.Column(
                        "reservation_applied",
                        sa.Boolean(),
                        nullable=False,
                        server_default=sa.false(),
                    )
                )
            if not _has_column(inspector, "sale_line", "quantity_mode"):
                batch_op.add_column(
                    sa.Column(
                        "quantity_mode",
                        sa.String(length=10),
                        nullable=False,
                        server_default="BOX",
                    )
                )

        inspector = inspect(bind)
        if not _has_index(inspector, "sale_line", "ix_sale_line_reservation_applied"):
            op.create_index(
                "ix_sale_line_reservation_applied",
                "sale_line",
                ["reservation_applied"],
                unique=False,
            )

    if {"inventory", "sale", "sale_line"}.issubset(table_names):
        op.execute(
            """
            UPDATE sale_line
            SET quantity_mode = 'BOX'
            WHERE quantity_mode IS NULL
            """
        )
        op.execute(
            """
            UPDATE sale_line
            SET reservation_applied = 1
            WHERE is_active = 1
              AND inventory_applied = 0
              AND sale_id IN (
                  SELECT id
                  FROM sale
                  WHERE is_active = 1
                    AND status = 'DRAFT'
              )
            """
        )
        op.execute("UPDATE inventory SET reserved_stock = 0")
        op.execute(
            """
            UPDATE inventory
            SET reserved_stock = (
                SELECT COALESCE(SUM(sale_line.quantity_units), 0)
                FROM sale_line
                JOIN sale ON sale.id = sale_line.sale_id
                WHERE sale_line.inventory_id = inventory.id
                  AND sale_line.is_active = 1
                  AND sale_line.reservation_applied = 1
                  AND sale.is_active = 1
                  AND sale.status = 'DRAFT'
            )
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = inspector.get_table_names()

    if "sale_line" in table_names:
        if _has_index(inspector, "sale_line", "ix_sale_line_reservation_applied"):
            op.drop_index("ix_sale_line_reservation_applied", table_name="sale_line")
        with op.batch_alter_table("sale_line") as batch_op:
            if _has_column(inspector, "sale_line", "quantity_mode"):
                batch_op.drop_column("quantity_mode")
            if _has_column(inspector, "sale_line", "reservation_applied"):
                batch_op.drop_column("reservation_applied")

    inspector = inspect(bind)
    if "sale" in table_names:
        if _has_fk(inspector, "sale", "fk_sale_cancelled_by_user"):
            op.drop_constraint("fk_sale_cancelled_by_user", "sale", type_="foreignkey")
        if _has_fk(inspector, "sale", "fk_sale_paid_by_user"):
            op.drop_constraint("fk_sale_paid_by_user", "sale", type_="foreignkey")
        with op.batch_alter_table("sale") as batch_op:
            if _has_column(inspector, "sale", "cancelled_at"):
                batch_op.drop_column("cancelled_at")
            if _has_column(inspector, "sale", "paid_at"):
                batch_op.drop_column("paid_at")
            if _has_column(inspector, "sale", "cancelled_by"):
                batch_op.drop_column("cancelled_by")
            if _has_column(inspector, "sale", "paid_by"):
                batch_op.drop_column("paid_by")

    inspector = inspect(bind)
    if "inventory" in table_names and _has_column(inspector, "inventory", "reserved_stock"):
        with op.batch_alter_table("inventory") as batch_op:
            batch_op.drop_column("reserved_stock")
