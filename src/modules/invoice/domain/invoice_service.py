from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.shared.enums.invoice_enums import InvoiceLinePriceType
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
    InventoryValueType,
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


def _constraint_name(err: IntegrityError) -> str | None:
    orig = getattr(err, "orig", None)
    diag = getattr(orig, "diag", None)
    return getattr(diag, "constraint_name", None) or getattr(
        orig, "constraint_name", None
    )


class InvoiceService:
    def __init__(self, repository: InvoiceRepository) -> None:
        self.repository = repository

    def _normalize_line_price(
        self,
        price: Decimal,
        price_type: InvoiceLinePriceType,
        box_size: int,
    ) -> Decimal:
        if price_type == InvoiceLinePriceType.UNIT:
            return price * Decimal(box_size)
        return price

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

    def _line_stock_quantity(self, line: InvoiceLine) -> int:
        # In this system, `Inventory.stock` represents PACKAGES/BOXES for a given `box_size`.
        return line.quantity_boxes

    def _compute_recent_avg_cost(
        self,
        movement_repository: InventoryMovementRepository,
        inventory_id: int,
        incoming_qty: int,
        incoming_unit_value: Decimal,
    ) -> Decimal:
        # This is a purchase-reference heuristic, not a pricing engine or accounting-grade cost.
        # The business only needs a recent reference of how the product has been bought.
        recent_qty, recent_cost = movement_repository.get_recent_in_effective_totals(
            inventory_id=inventory_id, months=6
        )
        total_qty = recent_qty + incoming_qty
        if total_qty <= 0:
            return incoming_unit_value
        return (recent_cost + (Decimal(incoming_qty) * incoming_unit_value)) / Decimal(
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

            quantity = self._line_stock_quantity(line)
            if quantity <= 0:
                continue

            inventory = inventory_repository.get_by_keys(
                warehouse_id=invoice.warehouse_id,
                product_id=line.product_id,
                box_size=line.box_size,
            )

            # Pricing agreement: invoices send `price` as the cost per box/presentation,
            # so the inventory movement value matches the line price (no multiplication by box_size).
            unit_value = line.price
            if inventory is None:
                inventory = Inventory(
                    stock=0,
                    box_size=line.box_size,
                    avg_cost=unit_value,
                    last_cost=unit_value,
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
            inventory.last_cost = unit_value
            inventory.avg_cost = (
                self._compute_recent_avg_cost(
                    movement_repository=movement_repository,
                    inventory_id=inventory.id,
                    incoming_qty=quantity,
                    incoming_unit_value=unit_value,
                )
            )

            movement = InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.INVOICE,
                event_type=InventoryEventType.INVOICE_RECEIVED,
                movement_type=InventoryMovementType.IN_,
                value_type=InventoryValueType.COST,
                quantity=quantity,
                unit_value=unit_value,
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

            quantity = self._line_stock_quantity(line)
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

            movement = InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.INVOICE,
                event_type=InventoryEventType.INVOICE_UNRECEIVED,
                movement_type=InventoryMovementType.OUT,
                value_type=InventoryValueType.COST,
                quantity=quantity,
                unit_value=line.price,
                prev_stock=prev_stock,
                new_stock=new_stock,
                inventory_id=inventory.id,
                invoice_line_id=line.id,
            )

            line.inventory_applied = False
            session.add(movement)
            session.add(line)
            session.flush()

            recent_qty, recent_cost = movement_repository.get_recent_in_effective_totals(
                inventory_id=inventory.id, months=6
            )
            latest_cost = movement_repository.get_latest_in_effective_value(inventory.id)
            if recent_qty > 0:
                inventory.avg_cost = recent_cost / Decimal(recent_qty)
            elif latest_cost is not None:
                inventory.avg_cost = latest_cost

            if latest_cost is not None:
                inventory.last_cost = latest_cost

            inventory_repository.update(inventory, commit=False)

            movement_sequence += 1

    def list_invoices(self, skip: int = 0, limit: Optional[int] = None):
        return self.repository.list(skip=skip, limit=limit)

    def get_invoice(self, invoice_id: int):
        return self._get_invoice_or_404(invoice_id)

    def create_invoice(self, payload: InvoiceCreateWithLines) -> Invoice:
        if payload.status not in {InvoiceStatus.DRAFT, InvoiceStatus.ARRIVED}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invoice must be created in DRAFT or ARRIVED status.",
            )

        session = self.repository.db
        invoice = Invoice(
            invoice_number=payload.invoice_number,
            sequence=payload.sequence,
            invoice_date=payload.invoice_date,
            order_date=payload.order_date,
            arrival_date=payload.arrival_date,
            status=payload.status,
            dollar_exchange_rate=payload.dollar_exchange_rate,
            logistic_tax=payload.general_expenses,
            approximate_profit_rate=payload.approximate_profit_rate,
            notes=payload.notes,
            warehouse_id=payload.warehouse_id,
        )

        # Create lines only if provided
        for l in payload.lines:
            total_units = l.box_size * l.quantity_boxes
            normalized_price = self._normalize_line_price(
                price=l.price,
                price_type=l.price_type,
                box_size=l.box_size,
            )
            invoice.lines.append(
                InvoiceLine(
                    product_id=l.product_id,
                    box_size=l.box_size,
                    quantity_boxes=l.quantity_boxes,
                    total_units=total_units,
                    price=normalized_price,
                    price_type=l.price_type,
                )
            )

        try:
            # Avoid `InvalidRequestError: A transaction is already begun on this Session.`
            # SQLAlchemy sessions auto-begin a transaction on first DB interaction,
            # so using `with session.begin()` here breaks if the caller already
            # executed a SELECT in the same session (e.g., seed scripts).
            session.add(invoice)
            session.flush()

            if payload.status == InvoiceStatus.ARRIVED:
                self._apply_invoice_received(invoice)

            session.commit()
        except IntegrityError as e:
            session.rollback()
            # Translate DB constraint errors to HTTP
            state = _sqlstate(e)
            if state == "23505":
                constraint = _constraint_name(e)
                if constraint == "uq_invoice_sequence":
                    detail = "Invoice number or sequence already exists"
                else:
                    detail = "Unique constraint violated"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail,
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
        except Exception:
            session.rollback()
            raise

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
        if "general_expenses" in data:
            data["logistic_tax"] = data.pop("general_expenses")

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
        normalized_price = self._normalize_line_price(
            price=payload.price,
            price_type=payload.price_type,
            box_size=payload.box_size,
        )
        line = InvoiceLine(
            product_id=payload.product_id,
            box_size=payload.box_size,
            quantity_boxes=payload.quantity_boxes,
            total_units=total_units,
            price=normalized_price,
            price_type=payload.price_type,
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
        if "price" in data or "price_type" in data:
            next_price = data.get("price", line.price)
            next_price_type = data.get("price_type", line.price_type)
            next_box_size = data.get("box_size", line.box_size)
            data["price"] = self._normalize_line_price(
                price=next_price,
                price_type=next_price_type,
                box_size=next_box_size,
            )

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
