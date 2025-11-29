from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


##### BASE
class ClientBase(BaseModel):
    name: str = Field(min_length=2, max_length=250)
    email: EmailStr = Field(min_length=5, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=13, min_length=7)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        """Normalize email: strip + lowercase."""
        if value is None:
            return value
        return str(value).strip().lower()


##### INPUTS
class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    email: Optional[EmailStr] = Field(default=None, min_length=5, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=13, min_length=7)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return value
        return str(value).strip().lower()

##### OUTPUTS
class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
