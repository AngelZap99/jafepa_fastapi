from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from typing import Optional
from src.shared.database.dependencies import SessionDep

from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryCreateWithProduct,
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


def _parse_csv_ids(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None

    stripped = raw_value.strip()
    if not stripped:
        return None

    values: list[int] = []
    for token in stripped.split(","):
        item = token.strip()
        if not item:
            continue
        if not item.isdigit():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "exclude_ids must be a comma-separated list of integers",
                    "errors": [
                        {
                            "field": "exclude_ids",
                            "message": "Invalid inventory id list format",
                        }
                    ],
                },
            )
        values.append(int(item))
    return values or None


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


@router.post(
    "/create-with-product",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_with_product(
    payload: InventoryCreateWithProduct = Depends(InventoryCreateWithProduct.as_form),
    image_file: UploadFile | None = File(None),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.create_inventory_with_product(payload, image=image_file)


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
    categoria: Optional[str] = Query(None, description="Filtra por categoría"),
    marca: Optional[str] = Query(None, description="Filtra por marca"),
    almacen: Optional[str] = Query(None, description="Filtra por almacén"),
    buscar: Optional[str] = Query(None, description="Buscar por nombre o código"),
    exclude_ids: Optional[str] = Query(
        None,
        description="IDs de inventario excluidos, en formato CSV: 10,11,15",
    ),
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    filters = {
        "categoria": categoria,
        "marca": marca,
        "almacen": almacen,
        "buscar": buscar,
        "exclude_ids": _parse_csv_ids(exclude_ids),
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    return inventory_service.generate_all_inventory_pdf(filters=filters)
