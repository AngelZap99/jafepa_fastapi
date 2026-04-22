from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.shared.enums.sale_enums import (
    SaleLinePriceType,
    SaleLineQuantityMode,
    SaleStatus,
)
from src.shared.schemas.common_responses import (
    ProductLineResponse,
    WarehouseLineResponse,
    ClientLineResponse,
    UserAuditLineResponse,
)
from src.shared.schemas.datetime_types import UTCDateTime


class SaleLineBase(BaseModel):
    inventory_id: int = Field(gt=0)
    quantity_boxes: Optional[int] = Field(default=None, gt=0)
    quantity_units: Optional[int] = Field(default=None, gt=0)
    price: Decimal = Field(ge=Decimal("0.00"))
    price_type: SaleLinePriceType = Field(default=SaleLinePriceType.BOX)

    @model_validator(mode="after")
    def validate_quantity(self):
        if self.quantity_boxes is None and self.quantity_units is None:
            raise ValueError("Debes enviar la cantidad en cajas o la cantidad en piezas")
        if self.quantity_boxes is not None and self.quantity_units is not None:
            raise ValueError("Solo puedes enviar una cantidad: en cajas o en piezas, no ambas")
        return self


class SaleLineCreate(SaleLineBase):
    model_config = ConfigDict(extra="forbid")
    pass


class SaleLineReplace(SaleLineBase):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = Field(default=None, gt=0)


class SaleLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_id: Optional[int] = Field(default=None, gt=0)
    quantity_boxes: Optional[int] = Field(default=None, gt=0)
    quantity_units: Optional[int] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    price_type: Optional[SaleLinePriceType] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Debes enviar al menos un campo")
        if self.quantity_boxes is not None and self.quantity_units is not None:
            raise ValueError("Solo puedes enviar una cantidad: en cajas o en piezas, no ambas")
        return self


class SaleLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    inventory_id: int
    quantity_boxes: int
    box_size: int
    price: Decimal
    price_type: SaleLinePriceType
    quantity_mode: SaleLineQuantityMode
    unit_price: Decimal
    box_price: Decimal
    total_price: Decimal
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    reservation_applied: bool
    inventory_applied: bool
    source_box_size: Optional[int] = None
    projected_units_from_stock: Optional[int] = None
    projected_boxes_to_open: Optional[int] = None
    projected_units_leftover: Optional[int] = None
    is_active: bool
    created_at: UTCDateTime
    updated_at: UTCDateTime

    inventory: Optional["SaleLineInventoryRef"] = None


class SaleLineInventoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock: int
    reserved_stock: int
    box_size: int
    product: Optional[ProductLineResponse] = None
    warehouse: Optional[WarehouseLineResponse] = None


class SaleBase(BaseModel):
    sale_date: date
    status: SaleStatus = SaleStatus.DRAFT
    notes: Optional[str] = Field(default=None, max_length=500)
    client_id: int = Field(gt=0)


class SaleCreateWithLines(SaleBase):
    model_config = ConfigDict(extra="forbid")

    sale_date: date = Field(default_factory=date.today)
    lines: List[SaleLineCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lines(self):
        return self


class SaleUpdate(BaseModel):
    sale_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    client_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("Debes enviar al menos un campo")
        return self


class SaleUpdateStatus(BaseModel):
    status: SaleStatus


class SaleFullUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sale_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    client_id: int = Field(gt=0)
    status: SaleStatus
    lines: List[SaleLineReplace] = Field(default_factory=list)


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_date: date
    status: SaleStatus
    total_price: Decimal
    notes: Optional[str]
    client_id: int
    client: Optional[ClientLineResponse] = None
    is_active: bool
    created_at: UTCDateTime
    updated_at: UTCDateTime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    paid_by: Optional[int] = None
    cancelled_by: Optional[int] = None
    paid_at: Optional[UTCDateTime] = None
    cancelled_at: Optional[UTCDateTime] = None
    created_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None
    paid_by_name: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    created_by_user: Optional[UserAuditLineResponse] = None
    paid_by_user: Optional[UserAuditLineResponse] = None
    cancelled_by_user: Optional[UserAuditLineResponse] = None

    lines: List[SaleLineResponse] = Field(default_factory=list)


class SaleReportFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_date: date
    to_date: date
    status: Optional[SaleStatus] = None
    client_id: Optional[int] = Field(default=None, gt=0)
    product_id: Optional[int] = Field(default=None, gt=0)
    warehouse_id: Optional[int] = Field(default=None, gt=0)
    inventory_id: Optional[int] = Field(default=None, gt=0)
    group_by: Optional[Literal["product", "warehouse", "client", "inventory"]] = None


class SaleReportTotals(BaseModel):
    sales_count: int
    total_boxes: int
    total_amount: Decimal


class SaleReportRow(BaseModel):
    group_by: str
    group_id: int
    group_label: str
    total_boxes: int
    total_amount: Decimal


class SaleReportSaleLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_id: int
    quantity_boxes: int
    box_size: int
    price: Decimal
    price_type: SaleLinePriceType
    unit_price: Decimal
    box_price: Decimal
    total_price: Decimal
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    inventory: Optional[SaleLineInventoryRef] = None


class SaleReportClientRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: Optional[str] = None


class SaleReportSaleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_date: date
    status: SaleStatus
    client: Optional[SaleReportClientRef] = None
    total_amount: Decimal
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    paid_by: Optional[int] = None
    cancelled_by: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None
    paid_by_name: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    lines: List[SaleReportSaleLine] = Field(default_factory=list)


class SaleReportResponse(BaseModel):
    period: dict
    filters: dict
    totals: SaleReportTotals
    rows: List[SaleReportRow] = Field(default_factory=list)
    sales: List[SaleReportSaleDetail] = Field(default_factory=list)
