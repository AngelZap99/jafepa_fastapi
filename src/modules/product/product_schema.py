from datetime import datetime
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, field_validator


##### BASE
def normalize_product_code(value):
    if value is None:
        return value
    return str(value).strip().upper()


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    code: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    category_id: int
    subcategory_id: Optional[int] = None
    brand_id: int

    # This stays as URL in DB/response. The file upload will be handled in router/service.
    image: Optional[str] = Field(default=None, max_length=500)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        return normalize_product_code(value)

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        code: str = Form(...),
        description: Optional[str] = Form(None),
        category_id: int = Form(...),
        subcategory_id: Optional[int] = Form(None),
        brand_id: int = Form(...),
        image: Optional[str] = Form(None),
    ) -> "ProductBase":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            brand_id=brand_id,
            image=image,
        )


##### INPUTS
class ProductCreate(ProductBase):
    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        code: str = Form(...),
        description: Optional[str] = Form(None),
        category_id: int = Form(...),
        subcategory_id: Optional[int] = Form(None),
        brand_id: int = Form(...),
        image: Optional[str] = Form(None),
    ) -> "ProductCreate":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            brand_id=brand_id,
            image=image,
        )


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
        return normalize_product_code(value)

    @classmethod
    def as_form(
        cls,
        name: Optional[str] = Form(None),
        code: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        category_id: Optional[int] = Form(None),
        subcategory_id: Optional[int] = Form(None),
        brand_id: Optional[int] = Form(None),
        image: Optional[str] = Form(None),
    ) -> "ProductUpdate":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            brand_id=brand_id,
            image=image,
        )


class ProductUpdateStatus(BaseModel):
    is_active: bool


##### OUTPUTS
class CategoryResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class BrandResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


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
