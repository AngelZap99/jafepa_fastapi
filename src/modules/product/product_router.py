from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.modules.product.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from src.modules.product.domain.product_service import ProductService
from src.modules.product.domain.product_repository import ProductRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)],
)


def get_product_service(session: SessionDep) -> ProductService:
    product_repository = ProductRepository(session)
    return ProductService(product_repository)


@router.get(
    "/list",
    response_model=list[ProductResponse],
    status_code=status.HTTP_200_OK,
)
def list_products(
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.list_products()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.get_product(product_id)


@router.post(
    "/create",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.create_product(payload)


@router.put(
    "/update/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.update_product(product_id, payload)


@router.delete(
    "/delete/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
def delete_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.delete_product(product_id)
