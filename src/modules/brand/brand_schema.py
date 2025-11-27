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

class BrandUpdateStatus(BaseModel):
    is_active: bool

##### OUTPUTS
class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
