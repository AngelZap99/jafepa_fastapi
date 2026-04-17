from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, UniqueConstraint

from src.shared.models.base_model import MyBaseModel


class Inventory(MyBaseModel, table=True):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint(
            "warehouse_id", "product_id", "box_size", name="uq_inventory_wh_product"
        ),
    )

    stock: int = Field(nullable=False)
    reserved_stock: int = Field(default=0, nullable=False)
    box_size: int = Field(nullable=False)
    avg_cost: Decimal = Field(
        default=Decimal("0.00"), sa_type=Numeric(12, 6), nullable=False
    )
    last_cost: Decimal = Field(
        default=Decimal("0.00"), sa_type=Numeric(12, 6), nullable=False
    )

    warehouse_id: int = Field(foreign_key="warehouse.id")
    product_id: int = Field(foreign_key="product.id")

    product: Mapped[Optional["Product"]] = Relationship(back_populates="inventory")
    warehouse: Mapped[Optional["Warehouse"]] = Relationship(back_populates="inventory")
