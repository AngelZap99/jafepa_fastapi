# src/shared/models/warehouse/warehouse_model.py

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func
from datetime import datetime

from src.shared.models.base_model import MyBaseModel
from src.shared.models.inventory.inventory_model import Inventory

class Warehouse(MyBaseModel, table=True):
    __tablename__ = "warehouse"

    name: str = Field(max_length=250, nullable=False)
    address: str = Field(max_length=250, nullable=False)
    inventory: Mapped[List[Inventory]] = Relationship(back_populates="warehouse")