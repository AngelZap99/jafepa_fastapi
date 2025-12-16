from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Numeric
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel

if TYPE_CHECKING:
    from src.shared.models.product.product_model import Product
    from src.shared.models.invoice.invoice_model import Invoice


class InvoiceLine(MyBaseModel, table=True):
    __tablename__ = "invoice_line"
    __table_args__ = (
        # Optional: prevents duplicated product rows per invoice (uncomment if you want this rule)
        # UniqueConstraint("invoice_id", "product_id", name="uq_invoice_line_invoice_product"),
    )

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
