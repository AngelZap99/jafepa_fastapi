# src/modules/warehouse/warehouse_router.py

from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.modules.warehouse.warehouse_schema import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from src.modules.warehouse.domain.warehouse_service import WarehouseService
from src.modules.warehouse.domain.warehouse_repository import WarehouseRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/warehouses",
    tags=["warehouses"],
    dependencies=[Depends(get_current_user)],
)


def get_warehouse_service(session: SessionDep) -> WarehouseService:
    warehouse_repository = WarehouseRepository(session)
    return WarehouseService(warehouse_repository)


@router.get(
    "/list",
    response_model=list[WarehouseResponse],
    status_code=status.HTTP_200_OK,
)
def list_warehouses(
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
):
    return warehouse_service.list_warehouses()


@router.get(
    "/{warehouse_id:int}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
)
def get_warehouse(
    warehouse_id: int,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
):
    return warehouse_service.get_warehouse(warehouse_id)


@router.post(
    "/create",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse(
    payload: WarehouseCreate,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
):
    return warehouse_service.create_warehouse(payload)


@router.put(
    "/update/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
):
    return warehouse_service.update_warehouse(warehouse_id, payload)


@router.delete(
    "/delete/{warehouse_id}",
    response_model=WarehouseResponse,
    status_code=status.HTTP_200_OK,
)
def delete_warehouse(
    warehouse_id: int,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
):
    return warehouse_service.delete_warehouse(warehouse_id)
