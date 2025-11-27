# src/modules/category/category_schema.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


##### BASE
class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    description: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = None


##### INPUTS
class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    description: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = None


class CategoryUpdateStatus(BaseModel):
    is_active: bool


##### OUTPUTS
class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
