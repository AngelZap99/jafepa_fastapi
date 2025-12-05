# src/modules/brand/brand_schema.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

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
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None  # Fecha de eliminación lógica
    is_active: bool = True                     # Estado activo/inactivo
