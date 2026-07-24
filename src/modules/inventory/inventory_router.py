from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from typing import Optional
from src.shared.database.dependencies import SessionDep

from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryCreateWithProduct,
    InventoryUpdate,
    InventoryResponse,
    InventoryMovementFilters,
    InventoryMovementListResponse,
    InventoryOperationalHistoryResponse,
)

from src.modules.inventory.domain.inventory_service import InventoryService
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.domain.inventory_history_xlsx import XLSX_CONTENT_TYPE

from src.modules.auth.auth_dependencies import get_current_user
from src.shared.enums.inventory_enums import InventoryMovementType
from src.shared.schemas.datetime_types import UTCDateTime


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
                    "message": "La lista de inventarios a excluir debe contener IDs separados por comas.",
                    "errors": [
                        {
                            "field": "exclude_ids",
                            "message": "El formato de la lista de IDs de inventario no es válido.",
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
    response_model=InventoryMovementListResponse,
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
    "/history/{inventory_id}",
    response_model=InventoryOperationalHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_inventory_operational_history(
    inventory_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=25, ge=1, le=100),
    movement_type: InventoryMovementType | None = Query(default=None),
    from_date: UTCDateTime | None = Query(default=None),
    to_date: UTCDateTime | None = Query(default=None),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    return inventory_service.get_operational_history(
        inventory_id=inventory_id,
        skip=skip,
        limit=limit,
        movement_type=movement_type,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/history/{inventory_id}/export",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
def export_inventory_operational_history(
    inventory_id: int,
    movement_type: InventoryMovementType | None = Query(default=None),
    from_date: UTCDateTime | None = Query(default=None),
    to_date: UTCDateTime | None = Query(default=None),
    inventory_service: InventoryService = Depends(get_inventory_service),
):
    content = inventory_service.export_operational_history_xlsx(
        inventory_id=inventory_id,
        movement_type=movement_type,
        from_date=from_date,
        to_date=to_date,
    )
    return Response(
        content=content,
        media_type=XLSX_CONTENT_TYPE,
        headers={
            "Content-Disposition": (
                f'attachment; filename="historial-inventario-{inventory_id}.xlsx"'
            )
        },
    )


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
    current_user=Depends(get_current_user),
):
    return inventory_service.create_inventory(payload, current_user=current_user)


@router.post(
    "/create-with-product",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_with_product(
    request: Request,
    payload: InventoryCreateWithProduct = Depends(InventoryCreateWithProduct.as_form),
    image_file: UploadFile | None = File(None),
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user=Depends(get_current_user),
):
    return inventory_service.create_inventory_with_product(
        payload,
        image=image_file,
        base_url=str(request.base_url),
        current_user=current_user,
    )


@router.put(
    "/update/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    current_user=Depends(get_current_user),
):
    return inventory_service.update_inventory(
        inventory_id, payload, current_user=current_user
    )


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
