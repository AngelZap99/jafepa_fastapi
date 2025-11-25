from fastapi import APIRouter

from src.modules.users.users_router import router as users_router


api_router = APIRouter()
api_router.include_router(users_router)


__all__ = ["api_router"]
