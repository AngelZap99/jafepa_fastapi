# src/shared/models/client/client_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel


class Client(MyBaseModel, table=True):
    __tablename__ = "client"

    name: str = Field(max_length=250)
    email: str = Field(max_length=50, unique=True)
    phone: Optional[str] = Field(default=None, max_length=13)
