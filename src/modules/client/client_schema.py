from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.shared.schemas.datetime_types import UTCDateTime


##### BASE
class ClientBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    email: Optional[EmailStr] = Field(default=None, min_length=5, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=13, min_length=7)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        """Normalize email: strip + lowercase."""
        if value is None:
            return value
        text = str(value).strip().lower()
        return None if not text else text

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return value
        text = str(value).strip()
        return None if not text else text


##### INPUTS
class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    email: Optional[EmailStr] = Field(default=None, min_length=5, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=13, min_length=7)
    is_active: Optional[bool] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return value
        text = str(value).strip().lower()
        return None if not text else text

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return value
        text = str(value).strip()
        return None if not text else text

##### OUTPUTS
class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    deleted_at: Optional[UTCDateTime] = None
    created_at: UTCDateTime
    updated_at: UTCDateTime
