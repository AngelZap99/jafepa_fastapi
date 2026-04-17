# src/modules/brand/brand_schema.py

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.datetime_types import UTCDateTime

##### BASE
class BrandBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)

##### INPUTS
class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    # Permitir actualizar active si se requiere
    is_active: Optional[bool] = None

##### OUTPUTS
class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: UTCDateTime
    updated_at: UTCDateTime
    deleted_at: Optional[UTCDateTime] = None  # Fecha de eliminación lógica
    is_active: bool = True                     # Estado activo/inactivo
