# src/modules/auth/dependencies.py

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.shared.database.dependencies import SessionDep
from src.shared.auth.jwt_auth import decode_token
from src.shared.models.user.user_model import User
from src.modules.users.domain.users_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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
            detail="Token has expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    repo = UserRepository(session)
    user = repo.get(int(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
