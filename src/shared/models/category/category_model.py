# src/shared/models/category/category_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel


class Category(MyBaseModel, table=True):
    __tablename__ = "category"

    # id heredado de MyBaseModel

    parent_id: Optional[int] = Field(default=None)

    name: str = Field(max_length=250, nullable=False)
    description: Optional[str] = Field(default=None, max_length=500)

    is_active: bool = Field(default=True)

    # sin ForeignKey también
    created_by: Optional[int] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()}
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
