# src/shared/models/warehouse/warehouse_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel

class Warehouse(MyBaseModel, table=True):
    __tablename__ = "warehouse"

    # id lo heredas de MyBaseModel

    name: str = Field(max_length=250, nullable=False)
    address: str = Field(max_length=250, nullable=False)

    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()}
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
