from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.datetime_types import UTCDateTime


##### BASE
class WarehouseBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    address: str = Field(min_length=5, max_length=250)
    email: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=25)


##### INPUTS
class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    address: Optional[str] = Field(default=None, min_length=5, max_length=250)
    email: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=25)
    is_active: Optional[bool] = None


##### OUTPUTS
class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    deleted_at: Optional[UTCDateTime] = None
    created_at: UTCDateTime
    updated_at: UTCDateTime
