from fastapi import APIRouter, Depends, status, Query

from src.shared.database.dependencies import SessionDep

from src.modules.invoice_line.invoice_line_schema import (
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from src.modules.invoice_line.domain.invoice_line_service import InvoiceLineService
from src.modules.invoice_line.domain.invoice_line_repository import (
    InvoiceLineRepository,
)

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/invoice-lines",
    tags=["invoice-lines"],
    dependencies=[Depends(get_current_user)],
)


def get_invoice_line_service(session: SessionDep) -> InvoiceLineService:
    repo = InvoiceLineRepository(session)
    return InvoiceLineService(repo)


@router.get(
    "/list/{invoice_id}",
    response_model=list[InvoiceLineResponse],
    status_code=status.HTTP_200_OK,
)
def list_invoice_lines(
    invoice_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    invoice_line_service: InvoiceLineService = Depends(get_invoice_line_service),
):
    return invoice_line_service.list_lines(
        invoice_id=invoice_id, skip=skip, limit=limit
    )


@router.post(
    "/create/{invoice_id}",
    response_model=InvoiceLineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice_line(
    invoice_id: int,
    payload: InvoiceLineCreate,
    invoice_line_service: InvoiceLineService = Depends(get_invoice_line_service),
):
    return invoice_line_service.create_line(invoice_id=invoice_id, payload=payload)


@router.put(
    "/update/{invoice_id}/{line_id}",
    response_model=InvoiceLineResponse,
    status_code=status.HTTP_200_OK,
)
def update_invoice_line(
    invoice_id: int,
    line_id: int,
    payload: InvoiceLineUpdate,
    invoice_line_service: InvoiceLineService = Depends(get_invoice_line_service),
):
    return invoice_line_service.update_line(
        invoice_id=invoice_id, line_id=line_id, payload=payload
    )


@router.delete(
    "/delete/{invoice_id}/{line_id}",
    response_model=InvoiceLineResponse,
    status_code=status.HTTP_200_OK,
)
def delete_invoice_line(
    invoice_id: int,
    line_id: int,
    invoice_line_service: InvoiceLineService = Depends(get_invoice_line_service),
):
    return invoice_line_service.delete_line(invoice_id=invoice_id, line_id=line_id)
