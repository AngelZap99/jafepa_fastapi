from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from src.shared.enums.invoice_enums import InvoiceLinePriceType
from src.shared.schemas.common_responses import (
    ProductLineResponse,
)
from src.shared.schemas.datetime_types import UTCDateTime


class InlineInvoiceProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=250)
    code: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category_id: int = Field(gt=0)
    brand_id: int = Field(gt=0)

    @model_validator(mode="after")
    def normalize_code(self):
        self.code = self.code.strip().upper()
        return self


class InvoiceLineBase(BaseModel):
    product_id: Optional[int] = Field(default=None, gt=0)
    new_product: Optional[InlineInvoiceProductCreate] = None
    box_size: int = Field(gt=0)
    quantity_boxes: int = Field(gt=0)
    total_units: Optional[int] = Field(default=None, gt=0)
    price: Decimal = Field(gt=Decimal("0.00"))
    price_type: InvoiceLinePriceType = InvoiceLinePriceType.BOX


class InvoiceLineCreate(InvoiceLineBase):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_total_units(self):
        if (self.product_id is None) == (self.new_product is None):
            raise ValueError("Debes enviar un producto existente o capturar un producto nuevo")
        if self.total_units is None:
            return self

        expected = self.box_size * self.quantity_boxes
        if self.total_units != expected:
            raise ValueError(
                "El total de unidades debe coincidir con la cantidad de cajas y el tamaño de caja"
            )
        return self


class InvoiceLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: Optional[int] = Field(default=None, gt=0)
    box_size: Optional[int] = Field(default=None, gt=0)
    quantity_boxes: Optional[int] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    price_type: Optional[InvoiceLinePriceType] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Debes enviar al menos un campo")
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
    price_type: InvoiceLinePriceType
    inventory_applied: bool
    is_active: bool
    created_at: UTCDateTime
    updated_at: UTCDateTime

    product: Optional[ProductLineResponse] = None

    @computed_field  # type: ignore[misc]
    @property
    def box_price(self) -> Decimal:
        return self.price

    @computed_field  # type: ignore[misc]
    @property
    def unit_price(self) -> Decimal:
        return self.price / Decimal(self.box_size)

    @computed_field  # type: ignore[misc]
    @property
    def total_price(self) -> Decimal:
        return self.price * Decimal(self.quantity_boxes)
