# src/modules/auth/dependencies.py

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.shared.database.dependencies import SessionDep
from src.shared.auth.jwt_auth import decode_token
from src.shared.models.user.user_model import User
from src.modules.users.domain.users_repository import UserRepository

# Routers are mounted under `/api` in `main.py`
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_optional_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", auto_error=False
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> User:
    from jwt import InvalidTokenError, ExpiredSignatureError

    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no es válido",
        )

    if payload.get("type") != "access":
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

    repo = UserRepository(session)
    user = repo.get(int(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario no existe o está inactivo",
        )

    return user


def get_optional_current_user(
    token: Annotated[str | None, Depends(oauth2_optional_scheme)],
    session: SessionDep,
) -> User | None:
    if not token:
        return None
    return get_current_user(token, session)
