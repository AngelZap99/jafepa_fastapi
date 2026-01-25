# src/shared/models/category/category_model.py

from typing import Optional
from sqlmodel import SQLModel, Field,Relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func
from datetime import datetime
from typing import List
from src.shared.models.base_model import MyBaseModel


class Category(MyBaseModel, table=True):
    __tablename__ = "category"

    parent_id: Optional[int] = Field(default=None)

    name: str = Field(max_length=250, nullable=False)
    description: Optional[str] = Field(default=None, max_length=500)
    products: Mapped[List["Product"]] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"foreign_keys": "[Product.category_id]"}
    )

    sub_products: Mapped[List["Product"]] = Relationship(
        back_populates="subcategory",
        sa_relationship_kwargs={"foreign_keys": "[Product.subcategory_id]"}
    )