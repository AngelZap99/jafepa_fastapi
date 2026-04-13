from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from src.shared.enums.sale_enums import SaleLinePriceType, SaleStatus
from src.shared.schemas.common_responses import (
    ProductLineResponse,
    WarehouseLineResponse,
    ClientLineResponse,
)


class SaleLineBase(BaseModel):
    inventory_id: int = Field(gt=0)
    quantity_boxes: int = Field(
        gt=0,
        validation_alias=AliasChoices("quantity_boxes", "quantity_units"),
    )
    price: Decimal = Field(gt=Decimal("0.00"))
    price_type: SaleLinePriceType = Field(default=SaleLinePriceType.BOX)


class SaleLineCreate(SaleLineBase):
    model_config = ConfigDict(extra="forbid")
    pass


class SaleLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_id: Optional[int] = Field(default=None, gt=0)
    quantity_boxes: Optional[int] = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("quantity_boxes", "quantity_units"),
    )
    price: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    price_type: Optional[SaleLinePriceType] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
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
    unit_price: Decimal
    box_price: Decimal
    total_price: Decimal
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    inventory_applied: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    inventory: Optional["SaleLineInventoryRef"] = None


class SaleLineInventoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
        if not self.lines:
            return self

        inventory_ids = [l.inventory_id for l in self.lines]
        if len(inventory_ids) != len(set(inventory_ids)):
            raise ValueError("Duplicate inventory_id in sale lines is not allowed")
        return self


class SaleUpdate(BaseModel):
    sale_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    client_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class SaleUpdateStatus(BaseModel):
    status: SaleStatus


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
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int] = None

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
    updated_by: Optional[int] = None
    lines: List[SaleReportSaleLine] = Field(default_factory=list)


class SaleReportResponse(BaseModel):
    period: dict
    filters: dict
    totals: SaleReportTotals
    rows: List[SaleReportRow] = Field(default_factory=list)
    sales: List[SaleReportSaleDetail] = Field(default_factory=list)
