from sqlmodel import Field, UniqueConstraint

from .base_model import MyBaseModel


class User(MyBaseModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="unique_user_email"),)

    # Personal information
    first_name: str = Field(max_length=30, nullable=False)
    last_name: str = Field(max_length=30, nullable=False)

    # Authentication information
    email: str = Field(max_length=50, nullable=False, index=True)
    password: str = Field(max_length=255, nullable=False)

    # Status information
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    is_admin: bool = Field(default=False)


__all__ = ["User"]
