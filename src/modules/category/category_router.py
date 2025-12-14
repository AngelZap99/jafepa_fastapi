# src/modules/category/categories_router.py

from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.modules.category.category_schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from src.modules.category.domain.category_service import CategoryService
from src.modules.category.domain.category_repository import CategoryRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    #dependencies=[Depends(get_current_user)],
)

def get_category_service(session: SessionDep) -> CategoryService:
    category_repository = CategoryRepository(session)
    return CategoryService(category_repository)


@router.get(
    "/list",
    response_model=list[CategoryResponse],
    status_code=status.HTTP_200_OK,
)
def list_categories(
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.list_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.get_category(category_id)


@router.post(
    "/create",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.create_category(payload)


@router.put(
    "/update/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.update_category(category_id, payload)


@router.delete(
    "/delete/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def delete_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service),
):
    return category_service.delete_category(category_id)
