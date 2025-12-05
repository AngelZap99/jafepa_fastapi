# src/shared/models/product/product_model.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from src.shared.models.base_model import MyBaseModel
from src.shared.models.category.category_model import Category
from src.shared.models.brand.brand_model import Brand

class Product(MyBaseModel, table=True):
    __tablename__ = "product"

    name: str = Field(max_length=250)
    code: str = Field(max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)

    category_id: int = Field(foreign_key="category.id")
    subcategory_id: Optional[int] = Field(default=None, foreign_key="category.id")
    brand_id: int = Field(foreign_key="brand.id")

    image: Optional[str] = Field(default=None, max_length=500)

    category: Optional[Category] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Product.category_id]"
        }
    )

    subcategory: Optional[Category] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Product.subcategory_id]"
        }
    )

    brand: Optional[Brand] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
