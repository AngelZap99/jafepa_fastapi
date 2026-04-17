from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.modules.product.product_schema import ProductResponse
from src.modules.warehouse.warehouse_schema import (
    WarehouseResponse,
)
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)


#######################################
# BASE
#######################################
class InventoryBase(BaseModel):
    stock: int = Field(ge=0)
    box_size: int = Field(ge=1)

    warehouse_id: int = Field(gt=0)
    product_id: int = Field(gt=0)


class InventoryCosts(BaseModel):
    avg_cost: Decimal = Field(ge=Decimal("0.00"))
    last_cost: Decimal = Field(ge=Decimal("0.00"))

    @field_validator("avg_cost", "last_cost", mode="before")
    @classmethod
    def normalize_cost(cls, value):
        if value is None:
            return value
        return Decimal(str(value))


#######################################
# INPUTS
#######################################
class InventoryCreate(InventoryBase):
    model_config = ConfigDict(extra="forbid")
    is_active: bool = True


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock: Optional[int] = Field(default=None, ge=0)
    box_size: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class InventoryCreateWithProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=250)
    code: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category_id: int = Field(gt=0)
    brand_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    stock: int = Field(ge=0)
    box_size: int = Field(ge=1)
    is_active: bool = True

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        if value is None:
            return value
        return str(value).strip().upper()

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        code: str = Form(...),
        description: Optional[str] = Form(None),
        category_id: int = Form(...),
        brand_id: int = Form(...),
        warehouse_id: int = Form(...),
        stock: int = Form(...),
        box_size: int = Form(...),
        is_active: bool = Form(True),
    ) -> "InventoryCreateWithProduct":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            warehouse_id=warehouse_id,
            stock=stock,
            box_size=box_size,
            is_active=is_active,
        )


class InventoryUpdateStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


#######################################
# OUTPUTS
#######################################
class InventoryResponse(InventoryBase, InventoryCosts):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Relaciones opcionales
    warehouse: Optional[WarehouseResponse] = None
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


#######################################
# MOVEMENT FILTERS/OUTPUTS
#######################################
class InventoryMovementFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_id: Optional[int] = Field(default=None, gt=0)
    product_id: Optional[int] = Field(default=None, gt=0)
    warehouse_id: Optional[int] = Field(default=None, gt=0)
    invoice_id: Optional[int] = Field(default=None, gt=0)
    invoice_line_id: Optional[int] = Field(default=None, gt=0)
    sale_id: Optional[int] = Field(default=None, gt=0)
    sale_line_id: Optional[int] = Field(default=None, gt=0)

    source_type: Optional[InventorySourceType] = None
    event_type: Optional[InventoryEventType] = None
    movement_type: Optional[InventoryMovementType] = None
    value_type: Optional[InventoryValueType] = None

    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

    include_inactive: bool = False


class InventoryMovementInventoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    box_size: int


class InventoryMovementInvoiceLineRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    product_id: int
    box_size: int
    quantity_boxes: int
    total_units: int
    price: Decimal


class InventoryMovementSaleLineRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    inventory_id: int
    quantity_units: int
    price: Decimal
    total_price: Decimal


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movement_date: datetime
    movement_group_id: str
    movement_sequence: int
    source_type: InventorySourceType
    event_type: InventoryEventType
    movement_type: InventoryMovementType
    value_type: InventoryValueType
    quantity: int
    unit_cost: Decimal
    prev_stock: int
    new_stock: int
    inventory_id: int
    invoice_line_id: Optional[int]
    sale_line_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    inventory: Optional[InventoryMovementInventoryRef] = None
    invoice_line: Optional[InventoryMovementInvoiceLineRef] = None
    sale_line: Optional[InventoryMovementSaleLineRef] = None
