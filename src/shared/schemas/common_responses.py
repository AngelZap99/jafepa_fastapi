from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WarehouseLineResponse(BaseModel):
    id: int
    name: str
    address: str
    email: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductLineResponse(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class ClientLineResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)
