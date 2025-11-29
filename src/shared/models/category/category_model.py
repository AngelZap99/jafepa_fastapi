# src/shared/models/category/category_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel


class Category(MyBaseModel, table=True):
    __tablename__ = "category"

    parent_id: Optional[int] = Field(default=None)

    name: str = Field(max_length=250, nullable=False)
    description: Optional[str] = Field(default=None, max_length=500)
