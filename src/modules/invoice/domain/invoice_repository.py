from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self, skip: int = 0, limit: Optional[int] = None, include_inactive: bool = True
    ) -> List[Invoice]:
        q = (
            self.db.query(Invoice)
            .options(
                selectinload(Invoice.lines).selectinload(InvoiceLine.product),
                selectinload(Invoice.warehouse),
            )
            .order_by(Invoice.id)
        )

        if not include_inactive:
            q = q.filter(Invoice.is_active == True)  # noqa: E712

        q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def get(self, invoice_id: int, include_inactive: bool = False) -> Optional[Invoice]:
        q = (
            self.db.query(Invoice)
            .options(
                selectinload(Invoice.lines).selectinload(InvoiceLine.product),
                selectinload(Invoice.warehouse),
            )
            .filter(Invoice.id == invoice_id)
        )

        if not include_inactive:
            q = q.filter(Invoice.is_active == True)  # noqa: E712

        return q.first()

    def add(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def update(self, invoice: Invoice) -> Invoice:
        # Ensure the instance is attached to the session
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def soft_delete(self, invoice: Invoice) -> Invoice:
        # Soft delete invoice and its lines
        invoice.is_active = False
        for line in invoice.lines:
            line.is_active = False

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def add_line(self, invoice: Invoice, line: InvoiceLine) -> InvoiceLine:
        # Attach line to invoice
        line.invoice_id = invoice.id
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def get_line(
        self, invoice_id: int, line_id: int, include_inactive: bool = False
    ) -> Optional[InvoiceLine]:
        q = (
            self.db.query(InvoiceLine)
            .options(selectinload(InvoiceLine.product))
            .filter(InvoiceLine.id == line_id, InvoiceLine.invoice_id == invoice_id)
        )

        if not include_inactive:
            q = q.filter(InvoiceLine.is_active == True)  # noqa: E712

        return q.first()

    def update_line(self, line: InvoiceLine) -> InvoiceLine:
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def soft_delete_line(self, line: InvoiceLine) -> InvoiceLine:
        line.is_active = False
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line
