# src/modules/auth/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status

from src.shared.database.dependencies import SessionDep
from src.modules.auth.auth_dto import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenPairResponse,
)
from src.modules.auth.domain.auth_service import AuthService
from src.modules.users.domain.users_repository import UserRepository

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def get_auth_service(session: SessionDep) -> AuthService:
    repo = UserRepository(session)
    return AuthService(repo)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return auth_service.refresh_tokens(payload.refresh_token)
    except Exception as e:  # noqa: F841
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
