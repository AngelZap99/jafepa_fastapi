from fastapi import APIRouter, Query, Depends, Request, status
from typing import Optional, List
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
    #dependencies=[Depends(get_current_user)],
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
    almacen: Optional[str] = Query(None, description="Filtra por almacén"),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    filters = {"almacen": almacen} if almacen is not None else None
    return inventory_service.list_inventory(skip=skip, limit=limit, filters=filters)


@router.get(
    "/movements",
    response_model=list[InventoryMovementResponse],
    status_code=status.HTTP_200_OK,
)
def list_inventory_movements(
    filters: InventoryMovementFilters = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
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
    request: Request,
    categoria: Optional[str] = Query(None, description="Filtra por categoría"),
    subcategoria: Optional[str] = Query(None, description="Filtra por subcategoría"),
    marca: Optional[str] = Query(None, description="Filtra por marca"),
    almacen: Optional[str] = Query(None, description="Filtra por almacén"),
    buscar: Optional[str] = Query(None, description="Buscar por nombre o código"),
    ids: Optional[List[int]] = Query(None, description="IDs de inventario seleccionados"),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    print("Query raw:", request.query_params)
    filters = {
        "categoria": categoria,
        "subcategoria": subcategoria,
        "marca": marca,
        "almacen": almacen,
        "buscar": buscar,
        "ids": ids
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    
    return inventory_service.generate_all_inventory_pdf(filters=filters)
