from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel
from src.shared.enums.invoice_enums import InvoiceStatus


class Invoice(MyBaseModel, table=True):
    __tablename__ = "invoice"
    __table_args__ = (
        UniqueConstraint("invoice_number", "sequence", name="uq_invoice_sequence"),
    )

    invoice_number: str = Field(max_length=50, nullable=False)
    sequence: int = Field(nullable=False, index=True)

    invoice_date: date = Field(default_factory=date.today, sa_type=Date, nullable=False)
    order_date: Optional[date] = Field(default=None, sa_type=Date)
    arrival_date: Optional[date] = Field(default=None, sa_type=Date)

    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, nullable=False)

    dollar_exchange_rate: Decimal = Field(
        default=Decimal("1.000000"), sa_type=Numeric(12, 6), nullable=False
    )
    logistic_tax: Decimal = Field(
        default=Decimal("0.00"), sa_type=Numeric(12, 2), nullable=False
    )

    notes: Optional[str] = Field(default=None, max_length=500)

    warehouse_id: int = Field(foreign_key="warehouse.id", nullable=False, index=True)

    # Use forward-ref strings to avoid circular imports
    warehouse: Mapped[Optional["Warehouse"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )

    lines: Mapped[List["InvoiceLine"]] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin",
            "order_by": "InvoiceLine.id",
        },
    )

    @property
    def general_expenses(self) -> Decimal:
        return self.logistic_tax

    @general_expenses.setter
    def general_expenses(self, value: Decimal) -> None:
        self.logistic_tax = value
