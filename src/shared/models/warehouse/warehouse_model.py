# src/shared/models/warehouse/warehouse_model.py

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel

class Warehouse(MyBaseModel, table=True):
    __tablename__ = "warehouse"

    name: str = Field(max_length=250, nullable=False)
    address: str = Field(max_length=250, nullable=False)