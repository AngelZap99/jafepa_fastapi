from __future__ import annotations

from src.modules.invoice.domain.invoice_repository import InvoiceRepository
from src.modules.invoice.domain.invoice_service import InvoiceService
from src.modules.invoice_line.invoice_line_schema import (
    InvoiceLineCreate,
    InvoiceLineUpdate,
)
from src.modules.invoice_line.domain.invoice_line_repository import (
    InvoiceLineRepository,
)


class InvoiceLineService:
    def __init__(self, repository: InvoiceLineRepository) -> None:
        self.repository = repository

    def _invoice_service(self) -> InvoiceService:
        return InvoiceService(InvoiceRepository(self.repository.db))

    def list_lines(self, invoice_id: int, skip: int = 0, limit: int | None = None):
        return self.repository.list_by_invoice(
            invoice_id=invoice_id, skip=skip, limit=limit
        )

    def create_line(self, invoice_id: int, payload: InvoiceLineCreate):
        return self._invoice_service().add_invoice_line(
            invoice_id=invoice_id, payload=payload
        )

    def update_line(self, invoice_id: int, line_id: int, payload: InvoiceLineUpdate):
        return self._invoice_service().update_invoice_line(
            invoice_id=invoice_id, line_id=line_id, payload=payload
        )

    def delete_line(self, invoice_id: int, line_id: int):
        return self._invoice_service().delete_invoice_line(
            invoice_id=invoice_id, line_id=line_id
        )
