# src/shared/models/client/client_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel


class Client(MyBaseModel, table=True):
    __tablename__ = "client"

    # Ya NO declares id (lo heredas de MyBaseModel)

    name: str = Field(max_length=250)
    email: str = Field(max_length=50, unique=True)
    phone: Optional[str] = Field(default=None, max_length=13)

    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
