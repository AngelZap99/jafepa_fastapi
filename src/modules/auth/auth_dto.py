# src/modules/auth/auth_dto.py

from pydantic import BaseModel, EmailStr, SecretStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

