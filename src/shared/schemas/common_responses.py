from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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


class UserAuditLineResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ErrorDetailResponse(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    message: str
    errors: list[ErrorDetailResponse] = Field(default_factory=list)
