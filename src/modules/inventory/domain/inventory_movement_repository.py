from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)


class InventoryMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self, movement: InventoryMovement, commit: bool = True
    ) -> InventoryMovement:
        self.db.add(movement)
        if commit:
            self.db.commit()
            self.db.refresh(movement)
        return movement

    def get_next_sequence(self, movement_group_id: str) -> int:
        last = (
            self.db.query(func.max(InventoryMovement.movement_sequence))
            .filter(InventoryMovement.movement_group_id == movement_group_id)
            .scalar()
        )
        return int(last or 0) + 1

    def list(
        self,
        skip: int = 0,
        limit: int | None = None,
        include_inactive: bool = False,
        inventory_id: int | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        invoice_id: int | None = None,
        invoice_line_id: int | None = None,
        sale_id: int | None = None,
        sale_line_id: int | None = None,
        source_type=None,
        event_type=None,
        movement_type=None,
        value_type=None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        q = self.db.query(InventoryMovement).options(
            selectinload(InventoryMovement.inventory),
            selectinload(InventoryMovement.invoice_line),
            selectinload(InventoryMovement.sale_line),
        )

        if not include_inactive:
            q = q.filter(InventoryMovement.is_active == True)  # noqa: E712

        if inventory_id is not None:
            q = q.filter(InventoryMovement.inventory_id == inventory_id)

        if invoice_line_id is not None:
            q = q.filter(InventoryMovement.invoice_line_id == invoice_line_id)

        if sale_line_id is not None:
            q = q.filter(InventoryMovement.sale_line_id == sale_line_id)

        if source_type is not None:
            q = q.filter(InventoryMovement.source_type == source_type)

        if event_type is not None:
            q = q.filter(InventoryMovement.event_type == event_type)

        if movement_type is not None:
            q = q.filter(InventoryMovement.movement_type == movement_type)

        if value_type is not None:
            q = q.filter(InventoryMovement.value_type == value_type)

        if from_date is not None:
            q = q.filter(InventoryMovement.movement_date >= from_date)

        if to_date is not None:
            q = q.filter(InventoryMovement.movement_date <= to_date)

        if product_id is not None or warehouse_id is not None:
            q = q.join(Inventory)
            if product_id is not None:
                q = q.filter(Inventory.product_id == product_id)
            if warehouse_id is not None:
                q = q.filter(Inventory.warehouse_id == warehouse_id)

        if invoice_id is not None:
            q = q.join(InvoiceLine).filter(InvoiceLine.invoice_id == invoice_id)

        if sale_id is not None:
            q = q.join(SaleLine).filter(SaleLine.sale_id == sale_id)

        q = q.order_by(
            InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()
        ).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def get_recent_in_totals(
        self, inventory_id: int, months: int = 12
    ) -> tuple[int, Decimal]:
        since_dt = datetime.utcnow() - timedelta(days=30 * months)
        qty_sum, cost_sum = (
            self.db.query(
                func.coalesce(func.sum(InventoryMovement.quantity), 0),
                func.coalesce(
                    func.sum(InventoryMovement.quantity * InventoryMovement.unit_cost),
                    Decimal("0"),
                ),
            )
            .filter(
                InventoryMovement.inventory_id == inventory_id,
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.movement_type == InventoryMovementType.IN_,
                InventoryMovement.source_type == InventorySourceType.INVOICE,
                InventoryMovement.event_type == InventoryEventType.INVOICE_RECEIVED,
                InventoryMovement.value_type == InventoryValueType.COST,
                InventoryMovement.movement_date >= since_dt,
            )
            .one()
        )
        return int(qty_sum), cost_sum

    def get_latest_in_unit_cost(
        self, inventory_id: int, months: int = 12
    ) -> Decimal | None:
        since_dt = datetime.utcnow() - timedelta(days=30 * months)
        row = (
            self.db.query(InventoryMovement.unit_cost)
            .filter(
                InventoryMovement.inventory_id == inventory_id,
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.movement_type == InventoryMovementType.IN_,
                InventoryMovement.source_type == InventorySourceType.INVOICE,
                InventoryMovement.event_type == InventoryEventType.INVOICE_RECEIVED,
                InventoryMovement.value_type == InventoryValueType.COST,
                InventoryMovement.movement_date >= since_dt,
            )
            .order_by(InventoryMovement.movement_date.desc())
            .first()
        )
        return row[0] if row else None

    def get_recent_out_totals(
        self, inventory_id: int, months: int = 12
    ) -> tuple[int, Decimal]:
        since_dt = datetime.utcnow() - timedelta(days=30 * months)
        qty_sum, cost_sum = (
            self.db.query(
                func.coalesce(func.sum(InventoryMovement.quantity), 0),
                func.coalesce(
                    func.sum(InventoryMovement.quantity * InventoryMovement.unit_cost),
                    Decimal("0"),
                ),
            )
            .filter(
                InventoryMovement.inventory_id == inventory_id,
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.movement_type == InventoryMovementType.OUT,
                InventoryMovement.source_type == InventorySourceType.SALE,
                InventoryMovement.event_type == InventoryEventType.SALE_APPROVED,
                InventoryMovement.value_type == InventoryValueType.PRICE,
                InventoryMovement.movement_date >= since_dt,
            )
            .one()
        )
        return int(qty_sum), cost_sum

    def get_latest_out_unit_cost(
        self, inventory_id: int, months: int = 12
    ) -> Decimal | None:
        since_dt = datetime.utcnow() - timedelta(days=30 * months)
        row = (
            self.db.query(InventoryMovement.unit_cost)
            .filter(
                InventoryMovement.inventory_id == inventory_id,
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.movement_type == InventoryMovementType.OUT,
                InventoryMovement.source_type == InventorySourceType.SALE,
                InventoryMovement.event_type == InventoryEventType.SALE_APPROVED,
                InventoryMovement.value_type == InventoryValueType.PRICE,
                InventoryMovement.movement_date >= since_dt,
            )
            .order_by(InventoryMovement.movement_date.desc())
            .first()
        )
        return row[0] if row else None

    def deactivate_invoice_line_in_movements(self, invoice_line_id: int) -> None:
        movements = (
            self.db.query(InventoryMovement)
            .filter(
                InventoryMovement.invoice_line_id == invoice_line_id,
                InventoryMovement.movement_type == InventoryMovementType.IN_,
                InventoryMovement.is_active == True,  # noqa: E712
            )
            .all()
        )
        for movement in movements:
            movement.is_active = False
