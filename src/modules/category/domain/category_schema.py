# src/modules/category/category_schema.py

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel

# -----------------------------
# BASE
# -----------------------------
class CategoryBase(SQLModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


# -----------------------------
# CREATE
# -----------------------------
class CategoryCreate(CategoryBase):
    pass


# -----------------------------
# UPDATE
# -----------------------------
class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


# -----------------------------
# RESPONSE
# -----------------------------
class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
