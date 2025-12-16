from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.shared.models.invoice.invoice_model import InvoiceStatus
from src.modules.invoice_line.invoice_line_schema import (
    InvoiceLineCreate,
    InvoiceLineResponse,
    WarehouseLineResponse,
)


class InvoiceBase(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    sequence: int = Field(gt=0)

    invoice_date: date
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None

    status: InvoiceStatus = InvoiceStatus.DRAFT

    dollar_exchange_rate: Decimal = Field(
        default=Decimal("1.000000"), ge=Decimal("0.000001")
    )
    logistic_tax: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))

    notes: Optional[str] = Field(default=None, max_length=500)

    warehouse_id: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        # Ensure dates follow a sensible timeline
        if self.order_date and self.order_date < self.invoice_date:
            raise ValueError("order_date cannot be earlier than invoice_date")
        if (
            self.arrival_date
            and self.order_date
            and self.arrival_date < self.order_date
        ):
            raise ValueError("arrival_date cannot be earlier than order_date")
        return self


class InvoiceCreateWithLines(InvoiceBase):
    model_config = ConfigDict(extra="forbid")

    # Lines are optional. If missing, invoice is created without lines.
    invoice_date: date = Field(default_factory=date.today)

    lines: List[InvoiceLineCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lines(self):
        # Allow empty lines, but prevent duplicated product rows if you want a clean invoice.
        if not self.lines:
            return self

        product_ids = [l.product_id for l in self.lines]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate product_id in invoice lines is not allowed")
        return self


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    sequence: Optional[int] = Field(default=None, gt=0)

    invoice_date: Optional[date] = None
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None

    status: Optional[InvoiceStatus] = None

    dollar_exchange_rate: Optional[Decimal] = Field(
        default=None, ge=Decimal("0.000001")
    )
    logistic_tax: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))

    notes: Optional[str] = Field(default=None, max_length=500)
    warehouse_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def at_least_one_field(self):
        # Prevent empty PATCH-like updates
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class InvoiceUpdateStatus(BaseModel):
    status: InvoiceStatus


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    sequence: int

    invoice_date: date
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None

    status: InvoiceStatus
    dollar_exchange_rate: Decimal
    logistic_tax: Decimal
    notes: Optional[str] = None

    warehouse_id: int

    is_active: bool
    created_at: datetime
    updated_at: datetime

    warehouse: Optional[WarehouseLineResponse] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)
