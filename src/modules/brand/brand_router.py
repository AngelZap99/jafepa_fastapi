from fastapi import APIRouter, Depends, status, Query

from src.shared.database.dependencies import SessionDep

from src.modules.brand.brand_schema import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
)
from src.modules.brand.domain.brand_service import BrandService
from src.modules.brand.domain.brand_repository import BrandRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/brands",
    tags=["brands"],
    #dependencies=[Depends(get_current_user)],
)


def get_brand_service(session: SessionDep) -> BrandService:
    repository = BrandRepository(session)
    return BrandService(repository)


# =========================
#        ROUTES
# =========================

@router.get(
    "/list",
    response_model=list[BrandResponse],
    status_code=status.HTTP_200_OK,
)
def list_brands(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    brand_service: BrandService = Depends(get_brand_service),
):
    return brand_service.list_brands(skip=skip, limit=limit)


@router.get(
    "/{brand_id:int}",
    response_model=BrandResponse,
    status_code=status.HTTP_200_OK,
)
def get_brand(
    brand_id: int,
    brand_service: BrandService = Depends(get_brand_service),
):
    return brand_service.get_brand(brand_id)


@router.post(
    "/create",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_brand(
    payload: BrandCreate,
    brand_service: BrandService = Depends(get_brand_service),
):
    return brand_service.create_brand(payload)


@router.put(
    "/update/{brand_id}",
    response_model=BrandResponse,
    status_code=status.HTTP_200_OK,
)
def update_brand(
    brand_id: int,
    payload: BrandUpdate,
    brand_service: BrandService = Depends(get_brand_service),
):
    return brand_service.update_brand(brand_id, payload)


@router.delete(
    "/delete/{brand_id}",
    response_model=BrandResponse,
    status_code=status.HTTP_200_OK,
)
def delete_brand(
    brand_id: int,
    brand_service: BrandService = Depends(get_brand_service),
):
    return brand_service.delete_brand(brand_id)
