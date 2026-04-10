from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status

from src.shared.enums.invoice_enums import InvoiceLinePriceType, InvoiceStatus
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
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

    def _normalize_price(
        self,
        price: Decimal,
        price_type: InvoiceLinePriceType,
        box_size: int,
    ) -> Decimal:
        if price_type == InvoiceLinePriceType.UNIT:
            return price * box_size
        return price

    def _get_line_or_404(self, invoice_id: int, line_id: int) -> InvoiceLine:
        line = self.repository.get(invoice_id=invoice_id, line_id=line_id)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice line not found",
            )
        return line

    def list_lines(self, invoice_id: int, skip: int = 0, limit: int | None = None):
        return self.repository.list_by_invoice(
            invoice_id=invoice_id, skip=skip, limit=limit
        )

    def create_line(self, invoice_id: int, payload: InvoiceLineCreate) -> InvoiceLine:
        # Create a line linked to a specific invoice
        invoice = self.repository.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )
        if invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )
        total_units = payload.box_size * payload.quantity_boxes
        normalized_price = self._normalize_price(
            price=payload.price,
            price_type=payload.price_type,
            box_size=payload.box_size,
        )
        line = InvoiceLine(
            invoice_id=invoice_id,
            product_id=payload.product_id,
            box_size=payload.box_size,
            quantity_boxes=payload.quantity_boxes,
            total_units=total_units,
            price=normalized_price,
            price_type=payload.price_type,
        )
        return self.repository.add(line)

    def update_line(
        self, invoice_id: int, line_id: int, payload: InvoiceLineUpdate
    ) -> InvoiceLine:
        line = self._get_line_or_404(invoice_id, line_id)
        if line.invoice and line.invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )
        data = payload.model_dump(exclude_unset=True)
        if "price" in data or "price_type" in data:
            next_price = data.get("price", line.price)
            next_price_type = data.get("price_type", line.price_type)
            next_box_size = data.get("box_size", line.box_size)
            data["price"] = self._normalize_price(
                price=next_price,
                price_type=next_price_type,
                box_size=next_box_size,
            )

        for field, value in data.items():
            setattr(line, field, value)

        if "box_size" in data or "quantity_boxes" in data:
            line.total_units = line.box_size * line.quantity_boxes

        return self.repository.update(line)

    def delete_line(self, invoice_id: int, line_id: int) -> InvoiceLine:
        line = self._get_line_or_404(invoice_id, line_id)
        if line.invoice and line.invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )
        return self.repository.soft_delete(line)
