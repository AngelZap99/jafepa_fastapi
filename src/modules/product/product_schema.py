from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

##### BASE
class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    code: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    category_id: int
    subcategory_id: Optional[int] = None
    brand_id: int

    image: Optional[str] = Field(default=None, max_length=500)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        if value is None:
            return value
        return str(value).strip().upper()


##### INPUTS
class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    brand_id: Optional[int] = None

    image: Optional[str] = Field(default=None, max_length=500)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        if value is None:
            return value
        return str(value).strip().upper()


class ProductUpdateStatus(BaseModel):
    is_active: bool


##### OUTPUTS

# Nuevos schemas para relaciones
class CategoryResponse(BaseModel):
    id: int
    name: str

class BrandResponse(BaseModel):
    id: int
    name: str


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Relaciones
    category: Optional[CategoryResponse] = None
    subcategory: Optional[CategoryResponse] = None
    brand: Optional[BrandResponse] = None

    model_config = ConfigDict(from_attributes=True)
