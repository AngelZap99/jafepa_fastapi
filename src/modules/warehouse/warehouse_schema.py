from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


##### BASE
class WarehouseBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    address: str = Field(min_length=5, max_length=250)


##### INPUTS
class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    address: Optional[str] = Field(default=None, min_length=5, max_length=250)


##### OUTPUTS
class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
