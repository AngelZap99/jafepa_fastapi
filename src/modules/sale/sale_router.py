from fastapi import APIRouter, Depends, status, Query

from src.modules.auth.auth_dependencies import get_current_user, get_optional_current_user
from src.shared.database.dependencies import SessionDep

from src.modules.sale.sale_schema import (
    SaleCreateWithLines,
    SaleUpdate,
    SaleUpdateStatus,
    SaleResponse,
    SaleLineCreate,
    SaleLineUpdate,
    SaleLineResponse,
    SaleReportFilters,
    SaleReportResponse,
)
from src.modules.sale.domain.sale_service import SaleService
from src.modules.sale.domain.sale_repository import SaleRepository


router = APIRouter(
    prefix="/sales",
    tags=["sales"],
    dependencies=[Depends(get_current_user)],
)


def get_sale_service(session: SessionDep) -> SaleService:
    sale_repository = SaleRepository(session)
    return SaleService(sale_repository)


@router.get(
    "/report",
    response_model=SaleReportResponse,
    status_code=status.HTTP_200_OK,
)
def get_sales_report(
    filters: SaleReportFilters = Depends(),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.get_sales_report(filters)


@router.get(
    "/list",
    response_model=list[SaleResponse],
    status_code=status.HTTP_200_OK,
)
def list_sales(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.list_sales(skip=skip, limit=limit)


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
)
def get_sale(
    sale_id: int,
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.get_sale(sale_id)


@router.get(
    "/{sale_id}/invoice",
    status_code=status.HTTP_200_OK,
)
def invoice_sale(
    sale_id: int,
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.generate_invoice_pdf(sale_id)


@router.post(
    "/create",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    payload: SaleCreateWithLines,
    current_user = Depends(get_optional_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.create_sale(payload, current_user)


@router.put(
    "/update/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
)
def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    current_user = Depends(get_optional_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.update_sale(sale_id, payload, current_user)


@router.put(
    "/update-status/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
)
def update_sale_status(
    sale_id: int,
    payload: SaleUpdateStatus,
    current_user = Depends(get_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.update_sale_status(sale_id, payload, current_user)


@router.delete(
    "/delete/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
)
def delete_sale(
    sale_id: int,
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.delete_sale(sale_id)


@router.post(
    "/{sale_id}/lines",
    response_model=SaleLineResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_sale_line(
    sale_id: int,
    payload: SaleLineCreate,
    current_user = Depends(get_optional_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.add_sale_line(sale_id, payload, current_user)


@router.put(
    "/{sale_id}/lines/{line_id}",
    response_model=SaleLineResponse,
    status_code=status.HTTP_200_OK,
)
def update_sale_line(
    sale_id: int,
    line_id: int,
    payload: SaleLineUpdate,
    current_user = Depends(get_optional_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.update_sale_line(sale_id, line_id, payload, current_user)


@router.delete(
    "/{sale_id}/lines/{line_id}",
    response_model=SaleLineResponse,
    status_code=status.HTTP_200_OK,
)
def delete_sale_line(
    sale_id: int,
    line_id: int,
    current_user = Depends(get_optional_current_user),
    sale_service: SaleService = Depends(get_sale_service),
):
    return sale_service.delete_sale_line(sale_id, line_id, current_user)
