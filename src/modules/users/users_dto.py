from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from modules.users.mixins.password_validation_mixin import PasswordValidationMixin


##### BASE
class UserBase(BaseModel):
    first_name: str = Field(min_length=2, max_length=30)
    last_name: str = Field(min_length=2, max_length=30)
    email: EmailStr = Field(min_length=5, max_length=50)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        """Normalize email address, removing leading and trailing whitespace and converting to lowercase."""
        if value is None:
            return value
        return str(value).strip().lower()


##### INPUTS
class UserCreateAdmin(UserBase, PasswordValidationMixin):
    is_admin: bool = True


class UserCreate(UserBase, PasswordValidationMixin):
    is_admin: bool = False


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[SecretStr] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return value
        return str(value).strip().lower()


class UserUpdateStatus(BaseModel):
    is_active: bool


class UserUpdateVerified(BaseModel):
    is_verified: bool


##### OUTPUTS
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
