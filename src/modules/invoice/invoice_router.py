from fastapi import APIRouter, Depends, status, Query

from src.shared.database.dependencies import SessionDep

from src.modules.invoice.invoice_schema import (
    InvoiceCreateWithLines,
    InvoiceUpdate,
    InvoiceUpdateStatus,
    InvoiceResponse,
)
from src.modules.invoice.domain.invoice_service import InvoiceService
from src.modules.invoice.domain.invoice_repository import InvoiceRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    dependencies=[Depends(get_current_user)],
)


def get_invoice_service(session: SessionDep) -> InvoiceService:
    invoice_repository = InvoiceRepository(session)
    return InvoiceService(invoice_repository)


@router.get(
    "/list",
    response_model=list[InvoiceResponse],
    status_code=status.HTTP_200_OK,
)
def list_invoices(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.list_invoices(skip=skip, limit=limit)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
def get_invoice(
    invoice_id: int,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.get_invoice(invoice_id)


@router.post(
    "/create",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    payload: InvoiceCreateWithLines,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.create_invoice(payload)


@router.put(
    "/update/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.update_invoice(invoice_id, payload)


@router.put(
    "/update-status/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceUpdateStatus,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.update_invoice_status(invoice_id, payload)


@router.delete(
    "/delete/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
)
def delete_invoice(
    invoice_id: int,
    invoice_service: InvoiceService = Depends(get_invoice_service),
):
    return invoice_service.delete_invoice(invoice_id)
