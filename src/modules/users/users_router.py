# src/modules/users/users_router.py
from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.shared.models.user.user_model import User
from src.modules.users.users_schema import (
    UserCreate,
    UserCreateAdmin,
    UserUpdate,
    UserResponse,
)
from src.modules.users.domain.users_service import UserService
from src.modules.users.domain.users_repository import UserRepository

from src.modules.auth.auth_dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # dependencies=[Depends(get_current_user)],
)


def get_user_service(session: SessionDep) -> UserService:
    user_repository = UserRepository(session)
    return UserService(user_repository)


@router.get(
    "/list",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def get_users(
    user_service: UserService = Depends(get_user_service),
):  # TODO: Implement pagination and optional search with filters
    return user_service.list_users()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.get_user(user_id)


@router.post(
    "/createUser",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.create_user(payload)


@router.post(
    "/createAdmin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin(
    payload: UserCreateAdmin,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.create_admin(payload)


@router.put(
    "/update/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_user(user_id, payload)


@router.delete(
    "/delete/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.delete_user(user_id)
