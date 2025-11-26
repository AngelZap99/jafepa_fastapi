# src/shared/models/brand/brand_model.py

from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy.sql import func
from src.shared.models.base_model import MyBaseModel

class Brand(MyBaseModel, table=True):
    __tablename__ = "brand"

    # id viene de MyBaseModel

    name: str = Field(max_length=250, nullable=False, unique=True)

    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()}
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
