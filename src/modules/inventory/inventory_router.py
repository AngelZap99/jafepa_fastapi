from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    InventoryMovementFilters,
    InventoryMovementResponse,
)

from src.modules.inventory.domain.inventory_service import InventoryService
from src.modules.inventory.domain.inventory_repository import InventoryRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(get_current_user)],
)


def get_inventory_service(session: SessionDep) -> InventoryService:
    repository = InventoryRepository(session)
    return InventoryService(repository)


@router.get(
    "/list",
    response_model=list[InventoryResponse],
    status_code=status.HTTP_200_OK,
)
def list_inventory(
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.list_inventory()


@router.get(
    "/movements",
    response_model=list[InventoryMovementResponse],
    status_code=status.HTTP_200_OK,
)
def list_inventory_movements(
    filters: InventoryMovementFilters = Depends(),
    skip: int = 0,
    limit: int = 100,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.list_movements(filters=filters, skip=skip, limit=limit)


@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_inventory(
    inventory_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.get_inventory(inventory_id)


@router.post(
    "/create",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    payload: InventoryCreate,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.create_inventory(payload)


@router.put(
    "/update/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.update_inventory(inventory_id, payload)


@router.delete(
    "/delete/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
)
def delete_inventory(
    inventory_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.delete_inventory(inventory_id)


# --------------------------
#      PDF EXPORT
# --------------------------
@router.get(
    "/pdf/all",
    status_code=status.HTTP_200_OK,
)
def generate_all_inventory_pdf(
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    return inventory_service.generate_all_inventory_pdf()
