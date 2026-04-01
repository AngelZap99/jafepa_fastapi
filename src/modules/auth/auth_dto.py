# src/modules/auth/auth_dto.py

from pydantic import BaseModel, EmailStr, SecretStr
from src.modules.users.users_schema import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenPairResponse):
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str
