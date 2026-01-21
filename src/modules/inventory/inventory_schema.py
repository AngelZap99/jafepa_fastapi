from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.modules.product.product_schema import ProductResponse
from src.modules.warehouse.warehouse_schema import (
    WarehouseResponse,
)
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
)


#######################################
# BASE
#######################################
class InventoryBase(BaseModel):
    stock: int = Field(ge=0)
    box_size: int = Field(ge=1)

    avg_cost: float = Field(ge=0)
    last_cost: float = Field(ge=0)

    warehouse_id: int = Field(gt=0)
    product_id: int = Field(gt=0)

    @field_validator("avg_cost", "last_cost", mode="before")
    @classmethod
    def normalize_cost(cls, value):
        if value is None:
            return value
        return float(value)


#######################################
# INPUTS
#######################################
class InventoryCreate(InventoryBase):
    model_config = ConfigDict(extra="forbid")
    pass


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock: Optional[int] = Field(default=None, ge=0)
    avg_cost: Optional[float] = Field(default=None, ge=0)
    last_cost: Optional[float] = Field(default=None, ge=0)

    @field_validator("avg_cost", "last_cost", mode="before")
    @classmethod
    def normalize_cost(cls, value):
        if value is None:
            return value
        return float(value)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class InventoryUpdateStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


#######################################
# OUTPUTS
#######################################
class InventoryResponse(InventoryBase):
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
