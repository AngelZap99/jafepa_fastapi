from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, AliasChoices, computed_field, model_validator

from src.shared.models.invoice.invoice_model import InvoiceStatus
from src.modules.invoice_line.invoice_line_schema import (
    InvoiceLineCreate,
    InvoiceLineResponse,
)
from src.shared.schemas.common_responses import (
    WarehouseLineResponse,
)


class InvoiceBase(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    sequence: int = Field(gt=0)

    invoice_date: date = Field(default_factory=date.today)
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None

    status: InvoiceStatus = InvoiceStatus.DRAFT

    dollar_exchange_rate: Decimal = Field(
        default=Decimal("1.000000"), ge=Decimal("0.000001")
    )
    general_expenses: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        validation_alias=AliasChoices("general_expenses", "logistic_tax"),
    )
    approximate_profit_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        validation_alias=AliasChoices(
            "approximate_profit_rate",
            "approximate_profit",
            "estimated_profit",
        ),
    )

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
        if not self.lines:
            return self

        keys = [(l.product_id, l.box_size) for l in self.lines]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate (product, box_size) in invoice lines is not allowed"
            )
        return self


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    sequence: Optional[int] = Field(default=None, gt=0)

    invoice_date: Optional[date] = None
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None

    dollar_exchange_rate: Optional[Decimal] = Field(
        default=None, ge=Decimal("0.000001")
    )
    general_expenses: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.00"),
        validation_alias=AliasChoices("general_expenses", "logistic_tax"),
    )
    approximate_profit_rate: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.00"),
        validation_alias=AliasChoices(
            "approximate_profit_rate",
            "approximate_profit",
            "estimated_profit",
        ),
    )

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
    general_expenses: Decimal
    approximate_profit_rate: Decimal
    notes: Optional[str] = None

    warehouse_id: int

    is_active: bool
    created_at: datetime
    updated_at: datetime

    warehouse: Optional[WarehouseLineResponse] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def subtotal(self) -> Decimal:
        return sum(
            (line.total_price for line in self.lines if line.is_active),
            Decimal("0.00"),
        )

    @computed_field  # type: ignore[misc]
    @property
    def general_expenses_total(self) -> Decimal:
        return (
            self.subtotal * self.general_expenses / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @computed_field  # type: ignore[misc]
    @property
    def approximate_profit_total(self) -> Decimal:
        return (
            self.subtotal * self.approximate_profit_rate / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @computed_field  # type: ignore[misc]
    @property
    def total(self) -> Decimal:
        return self.subtotal + self.general_expenses_total + self.approximate_profit_total
