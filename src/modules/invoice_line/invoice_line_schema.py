from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from src.shared.schemas.common_responses import (
    ProductLineResponse,
)


class InvoiceLineBase(BaseModel):
    product_id: int = Field(gt=0)
    box_size: int = Field(gt=0)
    quantity_boxes: int = Field(gt=0)
    total_units: Optional[int] = Field(default=None, gt=0)
    price: Decimal = Field(gt=Decimal("0.00"))


class InvoiceLineCreate(InvoiceLineBase):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_total_units(self):
        if self.total_units is None:
            return self

        expected = self.box_size * self.quantity_boxes
        if self.total_units != expected:
            raise ValueError("total_units must equal box_size * quantity_boxes")
        return self


class InvoiceLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: Optional[int] = Field(default=None, gt=0)
    box_size: Optional[int] = Field(default=None, gt=0)
    quantity_boxes: Optional[int] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    product_id: int
    box_size: int
    quantity_boxes: int
    total_units: int
    price: Decimal
    inventory_applied: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    product: Optional[ProductLineResponse] = None

    @computed_field  # type: ignore[misc]
    @property
    def total_price(self) -> Decimal:
        return self.price * Decimal(self.quantity_boxes)
