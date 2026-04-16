from typing import Optional

from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel
from typing import List


class Category(MyBaseModel, table=True):
    __tablename__ = "category"

    name: str = Field(max_length=250, nullable=False)
    description: Optional[str] = Field(default=None, max_length=500)
    products: Mapped[List["Product"]] = Relationship(back_populates="category")
