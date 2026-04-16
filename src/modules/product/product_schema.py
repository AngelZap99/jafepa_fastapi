from datetime import datetime
from decimal import Decimal
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
        brand_id: int = Form(...),
        image: Optional[str] = Form(None),
    ) -> "ProductBase":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
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
        brand_id: int = Form(...),
        image: Optional[str] = Form(None),
    ) -> "ProductCreate":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            image=image,
        )


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    category_id: Optional[int] = None
    brand_id: Optional[int] = None

    image: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None

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
        brand_id: Optional[int] = Form(None),
        image: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
    ) -> "ProductUpdate":
        return cls(
            name=name,
            code=code,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            image=image,
            is_active=is_active,
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
    brand: Optional[BrandResponse] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryStockItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_id: int
    product_id: int
    box_size: int
    stock: int
    available_boxes: int = 0
    avg_cost: Decimal
    last_cost: Decimal
    sales_last_price: Optional[float] = None
    sales_avg_price: Optional[float] = None
    is_active: bool


class ProductStockResponse(ProductResponse):
    stock_total: int = 0
    stock_boxes_total: int = 0
    inventory: list[InventoryStockItem] = Field(default_factory=list)
