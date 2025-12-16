from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel


class InvoiceLine(MyBaseModel, table=True):
    __tablename__ = "invoice_line"

    invoice_id: int = Field(foreign_key="invoice.id", nullable=False, index=True)
    product_id: int = Field(foreign_key="product.id", nullable=False, index=True)

    box_size: int = Field(nullable=False, gt=0)
    quantity_boxes: int = Field(nullable=False, gt=0)
    total_units: int = Field(nullable=False, gt=0)

    price: Decimal = Field(sa_type=Numeric(12, 2), nullable=False)

    invoice: Optional["Invoice"] = Relationship(
        back_populates="lines",
        sa_relationship_kwargs={"lazy": "joined"},
    )

    product: Optional["Product"] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
