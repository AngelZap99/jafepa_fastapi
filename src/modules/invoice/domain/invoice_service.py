from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
from src.modules.invoice.invoice_schema import (
    InvoiceCreateWithLines,
    InvoiceUpdate,
    InvoiceUpdateStatus,
)
from src.modules.invoice_line.invoice_line_schema import (
    InvoiceLineCreate,
    InvoiceLineUpdate,
)
from src.modules.invoice.domain.invoice_repository import InvoiceRepository


def _sqlstate(err: IntegrityError) -> str | None:
    # Tries common psycopg/psycopg2 attributes
    orig = getattr(err, "orig", None)
    return getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)


class InvoiceService:
    def __init__(self, repository: InvoiceRepository) -> None:
        self.repository = repository

    def _get_invoice_or_404(self, invoice_id: int) -> Invoice:
        invoice = self.repository.get(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
            )
        return invoice

    def _get_line_or_404(self, invoice_id: int, line_id: int) -> InvoiceLine:
        line = self.repository.get_line(invoice_id=invoice_id, line_id=line_id)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invoice line not found"
            )
        return line

    def list_invoices(self, skip: int = 0, limit: int = 100):
        return self.repository.list(skip=skip, limit=limit)

    def get_invoice(self, invoice_id: int):
        return self._get_invoice_or_404(invoice_id)

    def create_invoice(self, payload: InvoiceCreateWithLines) -> Invoice:
        invoice = Invoice(
            invoice_number=payload.invoice_number,
            sequence=payload.sequence,
            invoice_date=payload.invoice_date,
            order_date=payload.order_date,
            arrival_date=payload.arrival_date,
            status=payload.status,
            dollar_exchange_rate=payload.dollar_exchange_rate,
            logistic_tax=payload.logistic_tax,
            notes=payload.notes,
            warehouse_id=payload.warehouse_id,
        )

        # Create lines only if provided
        for l in payload.lines:
            invoice.lines.append(
                InvoiceLine(
                    product_id=l.product_id,
                    box_size=l.box_size,
                    quantity_boxes=l.quantity_boxes,
                    total_units=l.total_units,
                    price=l.price,
                )
            )

        try:
            self.repository.add(invoice)
        except IntegrityError as e:
            # Translate DB constraint errors to HTTP
            state = _sqlstate(e)
            if state == "23505":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Invoice number or sequence already exists",
                )
            if state == "23503":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid warehouse_id or product_id reference",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity constraint violated",
            )

        # Re-fetch with relationships eagerly loaded
        return self.repository.get(invoice.id, include_inactive=True)  # type: ignore[return-value]

    def update_invoice(self, invoice_id: int, payload: InvoiceUpdate) -> Invoice:
        invoice = self._get_invoice_or_404(invoice_id)
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(invoice, field, value)

        try:
            self.repository.update(invoice)
        except IntegrityError as e:
            state = _sqlstate(e)
            if state == "23505":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Invoice number or sequence already exists",
                )
            if state == "23503":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid warehouse_id reference",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity constraint violated",
            )

        return self._get_invoice_or_404(invoice_id)

    def update_invoice_status(
        self, invoice_id: int, payload: InvoiceUpdateStatus
    ) -> Invoice:
        invoice = self._get_invoice_or_404(invoice_id)
        invoice.status = payload.status
        self.repository.update(invoice)
        return self._get_invoice_or_404(invoice_id)

    def delete_invoice(self, invoice_id: int) -> Invoice:
        invoice = self._get_invoice_or_404(invoice_id)
        self.repository.soft_delete(invoice)
        return self.repository.get(invoice_id, include_inactive=True)  # type: ignore[return-value]

    # -------- Invoice lines (optional endpoints) --------

    def add_invoice_line(
        self, invoice_id: int, payload: InvoiceLineCreate
    ) -> InvoiceLine:
        invoice = self._get_invoice_or_404(invoice_id)

        line = InvoiceLine(
            product_id=payload.product_id,
            box_size=payload.box_size,
            quantity_boxes=payload.quantity_boxes,
            total_units=payload.total_units,
            price=payload.price,
        )

        try:
            return self.repository.add_line(invoice, line)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid product_id reference",
            )

    def update_invoice_line(
        self, invoice_id: int, line_id: int, payload: InvoiceLineUpdate
    ) -> InvoiceLine:
        line = self._get_line_or_404(invoice_id, line_id)
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(line, field, value)

        try:
            return self.repository.update_line(line)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid product_id reference",
            )

    def delete_invoice_line(self, invoice_id: int, line_id: int) -> InvoiceLine:
        line = self._get_line_or_404(invoice_id, line_id)
        return self.repository.soft_delete_line(line)
