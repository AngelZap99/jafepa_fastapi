from sqlmodel import Field, UniqueConstraint

from src.shared.models.base_model import MyBaseModel
from src.shared.models.user.user_roles import DEFAULT_USER_ROLE


class User(MyBaseModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="unique_user_email"),)

    # Personal information
    first_name: str = Field(max_length=30, nullable=False)
    last_name: str = Field(max_length=30, nullable=False)

    # Authentication information
    email: str = Field(max_length=50, nullable=False, index=True)
    password: str = Field(max_length=255, nullable=False)
    role: str = Field(default=DEFAULT_USER_ROLE.value, max_length=20, nullable=False)

    # Status information
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    is_admin: bool = Field(default=False)
