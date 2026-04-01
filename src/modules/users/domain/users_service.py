# src/modules/users/users_service.py

import logging
from typing import List

from fastapi import HTTPException, status
from passlib.context import CryptContext

from src.shared.models.user.user_model import User
from src.shared.models.user.user_roles import DEFAULT_ADMIN_ROLE
from src.modules.users.users_schema import (
    UserCreate,
    UserCreateAdmin,
    UserUpdate,
    UserUpdateStatus,
)
from src.modules.users.domain.users_repository import UserRepository


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


class UserService:
    ####################
    # Private methods
    ####################
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def _ensure_email_not_taken(
        self, email: str, user_owner_id: int | None = None
    ) -> None:
        emailUser = self.repository.get_by_email(email)
        if emailUser and (user_owner_id is None or emailUser.id != user_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {email} is already taken",
            )

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def _set_user_status(self, user_id: int, is_active: bool, source: str) -> User:
        user = self._get_user_or_404(user_id)
        previous_status = user.is_active
        user.is_active = is_active
        updated_user = self.repository.update(user)

        action = "activated" if updated_user.is_active else "deactivated"
        logger.warning(
            "User %s was %s via %s. previous_is_active=%s current_is_active=%s",
            updated_user.id,
            action,
            source,
            previous_status,
            updated_user.is_active,
        )
        return updated_user

    ####################
    # Public methods
    ####################
    def list_users(self, skip: int = 0, limit: int | None = None) -> List[User]:
        return self.repository.list(skip=skip, limit=limit)

    def get_user(self, user_id: int) -> User:
        return self._get_user_or_404(user_id)

    def create_user(self, payload: UserCreate) -> User:
        self._ensure_email_not_taken(payload.email)

        hashed_password = hash_password(payload.password.get_secret_value())

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password=hashed_password,
            role=payload.role.value,
            is_admin=False,
            is_active=True,
            is_verified=True,
        )

        return self.repository.add(user)

    def create_admin(self, payload: UserCreateAdmin) -> User:
        if self.repository.admin_exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An admin user already exists",
            )

        self._ensure_email_not_taken(payload.email)
        hashed_password = hash_password(payload.password.get_secret_value())

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password=hashed_password,
            role=payload.role.value if payload.role else DEFAULT_ADMIN_ROLE.value,
            is_admin=True,
            is_active=True,
            is_verified=True,
        )

        return self.repository.add(user)

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self._get_user_or_404(user_id)
        data = payload.model_dump(exclude_unset=True)

        if "email" in data:
            self._ensure_email_not_taken(data["email"], user_owner_id=user.id)

        if "password" in data and data["password"] is not None:
            data["password"] = hash_password(data["password"].get_secret_value())

        if "role" in data and data["role"] is not None:
            data["role"] = data["role"].value

        for field, value in data.items():
            setattr(user, field, value)

        return self.repository.update(user)

    def update_user_status(self, user_id: int, payload: UserUpdateStatus) -> User:
        return self._set_user_status(
            user_id=user_id,
            is_active=payload.is_active,
            source="status endpoint",
        )

    def delete_user(self, user_id: int) -> User:
        user = self._get_user_or_404(user_id)
        # Doesn't delete the user, just marks it as deleted
        user.is_active = False
        self.repository.update(user)
        return user
