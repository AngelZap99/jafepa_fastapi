# src/shared/models/inventory/inventory_model.py

from typing import Optional
from sqlmodel import SQLModel, Field,Relationship
from datetime import datetime

from src.shared.models.base_model import MyBaseModel

class Inventory(MyBaseModel, table=True):
    __tablename__ = "inventory"

    stock: int = Field(nullable=False)
    box_size: int = Field(nullable=False)
    avg_cost: float = Field(nullable=False)
    last_cost: float = Field(nullable=False)

    warehouse_id: int = Field(foreign_key="warehouse.id")
    product_id: int = Field(foreign_key="product.id")

    product: Optional["Product"] = Relationship(back_populates="inventory")
    warehouse: Optional["Warehouse"] = Relationship(back_populates="inventory")