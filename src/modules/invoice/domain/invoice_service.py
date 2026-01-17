from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
)
from src.shared.enums.invoice_enums import InvoiceStatus
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
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)


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

    def _line_total_units(self, line: InvoiceLine) -> int:
        return line.total_units or (line.box_size * line.quantity_boxes)

    def _compute_recent_avg_cost(
        self,
        movement_repository: InventoryMovementRepository,
        inventory_id: int,
        incoming_qty: int,
        incoming_unit_cost: Decimal,
    ) -> Decimal:
        recent_qty, recent_cost = movement_repository.get_recent_in_totals(
            inventory_id=inventory_id, months=6
        )
        total_qty = recent_qty + incoming_qty
        if total_qty <= 0:
            return incoming_unit_cost
        return (recent_cost + (Decimal(incoming_qty) * incoming_unit_cost)) / Decimal(
            total_qty
        )

    def _apply_invoice_received(self, invoice: Invoice) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)

        movement_group_id = str(uuid4())
        movement_sequence = 1

        for line in invoice.lines:
            if not line.is_active or line.inventory_applied:
                continue

            quantity = self._line_total_units(line)
            if quantity <= 0:
                continue

            inventory = inventory_repository.get_by_keys(
                warehouse_id=invoice.warehouse_id,
                product_id=line.product_id,
                box_size=line.box_size,
            )

            unit_cost = line.price
            if inventory is None:
                inventory = Inventory(
                    stock=0,
                    box_size=line.box_size,
                    avg_cost=float(unit_cost),
                    last_cost=float(unit_cost),
                    warehouse_id=invoice.warehouse_id,
                    product_id=line.product_id,
                    is_active=True,
                )
                inventory_repository.add(inventory, commit=False)
                session.flush()

            if not inventory.is_active:
                inventory.is_active = True

            prev_stock = inventory.stock
            new_stock = prev_stock + quantity
            inventory.stock = new_stock
            inventory.last_cost = float(unit_cost)
            inventory.avg_cost = float(
                self._compute_recent_avg_cost(
                movement_repository=movement_repository,
                inventory_id=inventory.id,
                incoming_qty=quantity,
                incoming_unit_cost=unit_cost,
            )
            )

            movement = InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.INVOICE,
                event_type=InventoryEventType.INVOICE_RECEIVED,
                movement_type=InventoryMovementType.IN_,
                quantity=quantity,
                unit_cost=unit_cost,
                prev_stock=prev_stock,
                new_stock=new_stock,
                inventory_id=inventory.id,
                invoice_line_id=line.id,
            )

            inventory_repository.update(inventory, commit=False)
            movement_repository.add(movement, commit=False)
            line.inventory_applied = True
            session.add(line)

            movement_sequence += 1

    def _apply_invoice_unreceived(self, invoice: Invoice) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)

        movement_group_id = str(uuid4())
        movement_sequence = 1

        for line in invoice.lines:
            if not line.is_active or not line.inventory_applied:
                continue

            quantity = self._line_total_units(line)
            if quantity <= 0:
                continue

            inventory = inventory_repository.get_by_keys(
                warehouse_id=invoice.warehouse_id,
                product_id=line.product_id,
                box_size=line.box_size,
            )
            if inventory is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory record not found for invoice line",
                )

            prev_stock = inventory.stock
            new_stock = prev_stock - quantity
            if new_stock < 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory stock cannot be negative",
                )

            inventory.stock = new_stock
            movement_repository.deactivate_invoice_line_in_movements(line.id)
            recent_qty, recent_cost = movement_repository.get_recent_in_totals(
                inventory_id=inventory.id, months=6
            )
            latest_cost = movement_repository.get_latest_in_unit_cost(inventory.id)
            if recent_qty > 0:
                inventory.avg_cost = float(recent_cost / Decimal(recent_qty))
            elif latest_cost is not None:
                inventory.avg_cost = float(latest_cost)

            if latest_cost is not None:
                inventory.last_cost = float(latest_cost)

            movement = InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.INVOICE,
                event_type=InventoryEventType.INVOICE_UNRECEIVED,
                movement_type=InventoryMovementType.OUT,
                quantity=quantity,
                unit_cost=line.price,
                prev_stock=prev_stock,
                new_stock=new_stock,
                inventory_id=inventory.id,
                invoice_line_id=line.id,
            )

            inventory_repository.update(inventory, commit=False)
            movement_repository.add(movement, commit=False)
            line.inventory_applied = False
            session.add(line)

            movement_sequence += 1

    def list_invoices(self, skip: int = 0, limit: int = 100):
        return self.repository.list(skip=skip, limit=limit)

    def get_invoice(self, invoice_id: int):
        return self._get_invoice_or_404(invoice_id)

    def create_invoice(self, payload: InvoiceCreateWithLines) -> Invoice:
        if payload.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invoice must be created in DRAFT status.",
            )
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
            total_units = l.box_size * l.quantity_boxes
            invoice.lines.append(
                InvoiceLine(
                    product_id=l.product_id,
                    box_size=l.box_size,
                    quantity_boxes=l.quantity_boxes,
                    total_units=total_units,
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
        if invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify an ARRIVED invoice. Revert status first.",
            )
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
        previous_status = invoice.status
        new_status = payload.status

        if previous_status == new_status:
            return invoice

        allowed_transitions = {
            InvoiceStatus.DRAFT: {InvoiceStatus.ARRIVED, InvoiceStatus.CANCELLED},
            InvoiceStatus.ARRIVED: {InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED},
            InvoiceStatus.CANCELLED: {InvoiceStatus.DRAFT},
        }
        if new_status not in allowed_transitions.get(previous_status, set()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid status transition.",
            )

        if new_status == InvoiceStatus.ARRIVED:
            self._apply_invoice_received(invoice)
        elif previous_status == InvoiceStatus.ARRIVED:
            self._apply_invoice_unreceived(invoice)

        invoice.status = new_status
        self.repository.db.add(invoice)
        self.repository.db.commit()
        self.repository.db.refresh(invoice)
        return self._get_invoice_or_404(invoice_id)

    def delete_invoice(self, invoice_id: int) -> Invoice:
        invoice = self._get_invoice_or_404(invoice_id)
        if invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete an ARRIVED invoice. Revert status first.",
            )
        self.repository.soft_delete(invoice)
        return self.repository.get(invoice_id, include_inactive=True)  # type: ignore[return-value]

    # -------- Invoice lines (optional endpoints) --------

    def add_invoice_line(
        self, invoice_id: int, payload: InvoiceLineCreate
    ) -> InvoiceLine:
        invoice = self._get_invoice_or_404(invoice_id)
        if invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )

        total_units = payload.box_size * payload.quantity_boxes
        line = InvoiceLine(
            product_id=payload.product_id,
            box_size=payload.box_size,
            quantity_boxes=payload.quantity_boxes,
            total_units=total_units,
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
        if line.invoice and line.invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(line, field, value)

        if "box_size" in data or "quantity_boxes" in data:
            line.total_units = line.box_size * line.quantity_boxes

        try:
            return self.repository.update_line(line)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid product_id reference",
            )

    def delete_invoice_line(self, invoice_id: int, line_id: int) -> InvoiceLine:
        line = self._get_line_or_404(invoice_id, line_id)
        if line.invoice and line.invoice.status == InvoiceStatus.ARRIVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify lines of an ARRIVED invoice. Revert status first.",
            )
        return self.repository.soft_delete_line(line)
