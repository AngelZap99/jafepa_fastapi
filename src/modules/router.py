from fastapi import APIRouter

from src.modules.users.users_router import router as users_router
from src.modules.auth.auth_router import router as auth_router


api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(auth_router)
