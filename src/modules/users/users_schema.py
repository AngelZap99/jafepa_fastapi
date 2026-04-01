from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from src.modules.users.users_mixins import PasswordValidationMixin
from src.shared.models.user.user_roles import (
    DEFAULT_ADMIN_ROLE,
    DEFAULT_USER_ROLE,
    UserRole,
)


##### BASE
class UserBase(BaseModel):
    first_name: str = Field(min_length=2, max_length=30)
    last_name: str = Field(min_length=2, max_length=30)
    email: EmailStr = Field(min_length=5, max_length=50)
    role: UserRole

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        """Normalize email address, removing leading and trailing whitespace and converting to lowercase."""
        if value is None:
            return value
        return str(value).strip().lower()


##### INPUTS
class UserCreateAdmin(UserBase, PasswordValidationMixin):
    role: UserRole = Field(default=DEFAULT_ADMIN_ROLE)


class UserCreate(UserBase, PasswordValidationMixin):
    role: UserRole = Field(default=DEFAULT_USER_ROLE)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[SecretStr] = None
    role: Optional[UserRole] = None

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
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
