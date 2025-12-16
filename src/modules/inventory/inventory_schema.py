from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.modules.product.product_schema import ProductResponse


#######################################
# BASE
#######################################
class InventoryBase(BaseModel):
    stock: int = Field(ge=0)
    box_size: int = Field(ge=1)

    avg_cost: float = Field(ge=0)
    last_cost: float = Field(ge=0)

    warehouse_id: int
    product_id: int

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
    pass


class InventoryUpdate(BaseModel):
    stock: Optional[int] = Field(default=None, ge=0)
    box_size: Optional[int] = Field(default=None, ge=1)

    avg_cost: Optional[float] = Field(default=None, ge=0)
    last_cost: Optional[float] = Field(default=None, ge=0)

    warehouse_id: Optional[int] = None
    product_id: Optional[int] = None

    @field_validator("avg_cost", "last_cost", mode="before")
    @classmethod
    def normalize_cost(cls, value):
        if value is None:
            return value
        return float(value)


class InventoryUpdateStatus(BaseModel):
    is_active: bool


#######################################
# OUTPUTS
#######################################
class WarehouseResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class InventoryResponse(InventoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Relaciones opcionales
    warehouse: Optional[WarehouseResponse] = None
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)
