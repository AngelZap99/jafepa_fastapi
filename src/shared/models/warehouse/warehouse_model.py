# src/shared/models/warehouse/warehouse_model.py

from typing import List, Optional

from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel
from src.shared.models.inventory.inventory_model import Inventory


class Warehouse(MyBaseModel, table=True):
    __tablename__ = "warehouse"

    name: str = Field(max_length=250, nullable=False)
    address: str = Field(max_length=250, nullable=False)

    email: Optional[str] = Field(default=None, max_length=50, nullable=True)
    phone: Optional[str] = Field(default=None, max_length=25, nullable=True)

    inventory: Mapped[List[Inventory]] = Relationship(back_populates="warehouse")
