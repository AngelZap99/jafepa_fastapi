from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum as SAEnum, Numeric
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.enums.sale_enums import SaleLinePriceType, SaleLineQuantityMode
from src.shared.models.base_model import MyBaseModel


class SaleLine(MyBaseModel, table=True):
    __tablename__ = "sale_line"

    sale_id: int = Field(foreign_key="sale.id", nullable=False, index=True)
    inventory_id: int = Field(foreign_key="inventory.id", nullable=False, index=True)

    quantity_units: int = Field(nullable=False, gt=0)
    box_size: int = Field(nullable=False, default=1)
    price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False)
    price_type: SaleLinePriceType = Field(
        sa_type=SAEnum(SaleLinePriceType, name="salelinepricetype"),
        default=SaleLinePriceType.BOX,
        nullable=False,
    )
    quantity_mode: SaleLineQuantityMode = Field(
        default=SaleLineQuantityMode.BOX,
        nullable=False,
    )
    unit_price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    box_price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False)
    product_code: Optional[str] = Field(default=None, max_length=100, index=True)
    product_name: Optional[str] = Field(default=None, max_length=250)

    reservation_applied: bool = Field(default=False, nullable=False, index=True)
    inventory_applied: bool = Field(default=False, nullable=False, index=True)

    sale: Mapped[Optional["Sale"]] = Relationship(
        back_populates="lines",
        sa_relationship_kwargs={"lazy": "joined"},
    )
    inventory: Mapped[Optional["Inventory"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )

    @property
    def quantity_boxes(self) -> int:
        return self.quantity_units

    @quantity_boxes.setter
    def quantity_boxes(self, value: int) -> None:
        self.quantity_units = value
