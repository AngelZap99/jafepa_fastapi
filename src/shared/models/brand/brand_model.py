# src/shared/models/brand/brand_model.py

from sqlmodel import SQLModel, Field,Relationship
from datetime import datetime
from sqlalchemy.sql import func
from src.shared.models.base_model import MyBaseModel
from typing import List
class Brand(MyBaseModel, table=True):
    __tablename__ = "brand"

    name: str = Field(max_length=250, nullable=False, unique=True)
    
    products: List["Product"] = Relationship(back_populates="brand")
