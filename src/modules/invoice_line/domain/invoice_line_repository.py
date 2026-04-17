from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine


class InvoiceLineRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_invoice(
        self,
        invoice_id: int,
        skip: int = 0,
        limit: int | None = None,
        include_inactive: bool = True,
    ) -> List[InvoiceLine]:
        q = (
            select(InvoiceLine)
            .options(selectinload(InvoiceLine.product))
            .where(InvoiceLine.invoice_id == invoice_id)
            .order_by(InvoiceLine.id)
        )

        if not include_inactive:
            q = q.where(InvoiceLine.is_active == True)  # noqa: E712

        q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return self.db.execute(q).scalars().all()

    def get(
        self,
        invoice_id: int,
        line_id: int,
        include_inactive: bool = False,
    ) -> Optional[InvoiceLine]:
        q = (
            select(InvoiceLine)
            .options(selectinload(InvoiceLine.product))
            .where(InvoiceLine.id == line_id, InvoiceLine.invoice_id == invoice_id)
        )

        if not include_inactive:
            q = q.where(InvoiceLine.is_active == True)  # noqa: E712

        return self.db.execute(q).scalars().first()

    def add(self, line: InvoiceLine) -> InvoiceLine:
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        return self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id, Invoice.is_active == True  # noqa: E712
            )
        ).scalars().first()

    def update(self, line: InvoiceLine) -> InvoiceLine:
        # Ensure the instance is attached to the session
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def soft_delete(self, line: InvoiceLine) -> InvoiceLine:
        line.is_active = False
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line
