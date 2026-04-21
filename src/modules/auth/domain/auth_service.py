# src/modules/auth/auth_service.py

from fastapi import HTTPException, status
from passlib.context import CryptContext

from src.shared.auth.jwt_auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.modules.auth.auth_dto import LoginRequest, LoginResponse, TokenPairResponse

from src.modules.users.domain.users_repository import UserRepository
from src.shared.models.user.user_model import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class AuthService:
    ####################
    # Private methods
    ####################
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def _authenticate_user(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario está inactivo",
            )

        return user

    ####################
    # Public methods
    ####################
    def login(self, payload: LoginRequest) -> LoginResponse:
        user = self._authenticate_user(
            email=payload.email,
            password=payload.password.get_secret_value(),
        )

        subject = str(user.id)
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenPairResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token de actualización no es válido",
            )

        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El tipo de token no es válido",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El contenido del token no es válido",
            )

        user = self.user_repository.get(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario no existe o está inactivo",
            )

        # Emitimos un nuevo access token, pero mantenemos el mismo refresh token.
        subject = str(user.id)
        new_access = create_access_token(subject)

        return TokenPairResponse(
            access_token=new_access,
            refresh_token=refresh_token,
        )
