from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WarehouseLineResponse(BaseModel):
    id: int
    name: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class ProductLineResponse(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)
