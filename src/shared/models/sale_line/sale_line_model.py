from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel


class SaleLine(MyBaseModel, table=True):
    __tablename__ = "sale_line"

    sale_id: int = Field(foreign_key="sale.id", nullable=False, index=True)
    inventory_id: int = Field(foreign_key="inventory.id", nullable=False, index=True)

    quantity_units: int = Field(nullable=False, gt=0)
    price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False)
    total_price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False)

    inventory_applied: bool = Field(default=False, nullable=False, index=True)

    sale: Mapped[Optional["Sale"]] = Relationship(
        back_populates="lines",
        sa_relationship_kwargs={"lazy": "joined"},
    )
    inventory: Mapped[Optional["Inventory"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
