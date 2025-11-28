# src/shared/models/product/product_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel


class Product(MyBaseModel, table=True):
    __tablename__ = "product"

    # Campos propios
    name: str = Field(max_length=250)
    code: str = Field(max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)

    # Llave foránea obligatoria: category
    category_id: int = Field(foreign_key="category.id")

    # Llave foránea opcional: subcategory (puede ir NULL)
    subcategory_id: Optional[int] = Field(default=None, foreign_key="category.id")

    # Llave foránea obligatoria: brand
    brand_id: int = Field(foreign_key="brand.id")

    # Imagen (int)
    image: Optional[int] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
