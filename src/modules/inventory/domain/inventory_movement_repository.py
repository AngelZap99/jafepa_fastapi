from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.invoice_line.invoice_line_model import InvoiceLine
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.sale.sale_model import Sale
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.utils.datetime import utcnow


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
            self.db.execute(
                select(func.max(InventoryMovement.movement_sequence)).where(
                    InventoryMovement.movement_group_id == movement_group_id
                )
            ).scalar()
        )
        return int(last or 0) + 1

    def _apply_filters(
        self,
        q,
        *,
        include_inactive: bool = False,
        inventory_id: int | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        created_by: int | None = None,
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

        if created_by is not None:
            actor_invoice_line = aliased(InvoiceLine)
            actor_invoice = aliased(Invoice)
            actor_sale_line = aliased(SaleLine)
            actor_sale = aliased(Sale)
            q = (
                q.outerjoin(
                    actor_invoice_line,
                    InventoryMovement.invoice_line_id == actor_invoice_line.id,
                )
                .outerjoin(actor_invoice, actor_invoice_line.invoice_id == actor_invoice.id)
                .outerjoin(actor_sale_line, InventoryMovement.sale_line_id == actor_sale_line.id)
                .outerjoin(actor_sale, actor_sale_line.sale_id == actor_sale.id)
                .filter(
                    or_(
                        InventoryMovement.created_by == created_by,
                        actor_sale.created_by == created_by,
                        actor_sale.updated_by == created_by,
                        actor_sale.paid_by == created_by,
                        actor_sale.cancelled_by == created_by,
                        actor_invoice.created_by == created_by,
                        actor_invoice.updated_by == created_by,
                    )
                )
            )

        return q

    def count(
        self,
        include_inactive: bool = False,
        inventory_id: int | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        created_by: int | None = None,
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
    ) -> int:
        q = select(func.count(InventoryMovement.id))
        q = self._apply_filters(
            q,
            include_inactive=include_inactive,
            inventory_id=inventory_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            created_by=created_by,
            invoice_id=invoice_id,
            invoice_line_id=invoice_line_id,
            sale_id=sale_id,
            sale_line_id=sale_line_id,
            source_type=source_type,
            event_type=event_type,
            movement_type=movement_type,
            value_type=value_type,
            from_date=from_date,
            to_date=to_date,
        )
        return int(self.db.execute(q).scalar() or 0)

    def list(
        self,
        skip: int = 0,
        limit: int | None = None,
        include_inactive: bool = False,
        inventory_id: int | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        created_by: int | None = None,
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
        q = select(InventoryMovement).options(
            selectinload(InventoryMovement.inventory),
            selectinload(InventoryMovement.invoice_line).selectinload(InvoiceLine.invoice),
            selectinload(InventoryMovement.sale_line).selectinload(SaleLine.sale),
        )
        q = self._apply_filters(
            q,
            include_inactive=include_inactive,
            inventory_id=inventory_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            created_by=created_by,
            invoice_id=invoice_id,
            invoice_line_id=invoice_line_id,
            sale_id=sale_id,
            sale_line_id=sale_line_id,
            source_type=source_type,
            event_type=event_type,
            movement_type=movement_type,
            value_type=value_type,
            from_date=from_date,
            to_date=to_date,
        )

        q = q.order_by(
            InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()
        ).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return self.db.execute(q).scalars().all()

    def _operational_conditions(
        self,
        *,
        inventory_id: int,
        movement_type=None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        latest_invoice_movement_ids = (
            select(func.max(InventoryMovement.id))
            .where(
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.source_type == InventorySourceType.INVOICE,
                InventoryMovement.invoice_line_id.is_not(None),
            )
            .group_by(InventoryMovement.invoice_line_id)
        )
        latest_sale_movement_ids = (
            select(func.max(InventoryMovement.id))
            .where(
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.source_type == InventorySourceType.SALE,
                InventoryMovement.sale_line_id.is_not(None),
            )
            .group_by(InventoryMovement.sale_line_id)
        )

        effective_external_movement = or_(
            and_(
                InventoryMovement.id.in_(latest_invoice_movement_ids),
                InventoryMovement.event_type
                == InventoryEventType.INVOICE_RECEIVED,
            ),
            and_(
                InventoryMovement.id.in_(latest_sale_movement_ids),
                InventoryMovement.event_type == InventoryEventType.SALE_APPROVED,
            ),
        )
        effective_manual_movement = and_(
            InventoryMovement.source_type == InventorySourceType.MANUAL,
            InventoryMovement.event_type.in_(
                [
                    InventoryEventType.MANUAL_CREATED,
                    InventoryEventType.MANUAL_STOCK_ADJUSTED,
                ]
            ),
            InventoryMovement.prev_stock != InventoryMovement.new_stock,
        )

        conditions = [
            InventoryMovement.is_active == True,  # noqa: E712
            InventoryMovement.inventory_id == inventory_id,
            or_(effective_external_movement, effective_manual_movement),
        ]
        if movement_type is not None:
            conditions.append(InventoryMovement.movement_type == movement_type)
        if from_date is not None:
            conditions.append(InventoryMovement.movement_date >= from_date)
        if to_date is not None:
            conditions.append(InventoryMovement.movement_date <= to_date)
        return conditions

    def list_operational(
        self,
        *,
        inventory_id: int,
        skip: int = 0,
        limit: int | None = None,
        movement_type=None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[InventoryMovement]:
        q = (
            select(InventoryMovement)
            .options(
                selectinload(InventoryMovement.invoice_line).selectinload(
                    InvoiceLine.invoice
                ),
                selectinload(InventoryMovement.sale_line)
                .selectinload(SaleLine.sale)
                .selectinload(Sale.client),
            )
            .where(
                *self._operational_conditions(
                    inventory_id=inventory_id,
                    movement_type=movement_type,
                    from_date=from_date,
                    to_date=to_date,
                )
            )
            .order_by(
                InventoryMovement.movement_date.desc(),
                InventoryMovement.id.desc(),
            )
            .offset(skip)
        )
        if limit is not None:
            q = q.limit(limit)
        return list(self.db.execute(q).scalars().all())

    def count_operational(
        self,
        *,
        inventory_id: int,
        movement_type=None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        q = select(func.count(InventoryMovement.id)).where(
            *self._operational_conditions(
                inventory_id=inventory_id,
                movement_type=movement_type,
                from_date=from_date,
                to_date=to_date,
            )
        )
        return int(self.db.execute(q).scalar() or 0)

    def operational_totals(
        self,
        *,
        inventory_id: int,
        movement_type=None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[int, int]:
        q = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            InventoryMovement.movement_type
                            == InventoryMovementType.IN_,
                            InventoryMovement.quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            InventoryMovement.movement_type
                            == InventoryMovementType.OUT,
                            InventoryMovement.quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
        ).where(
            *self._operational_conditions(
                inventory_id=inventory_id,
                movement_type=movement_type,
                from_date=from_date,
                to_date=to_date,
            )
        )
        entries, exits = self.db.execute(q).one()
        return int(entries or 0), int(exits or 0)

    def _effective_line_movements_subquery(
        self,
        *,
        inventory_id: int,
        source_type: InventorySourceType,
        value_type: InventoryValueType,
        line_field: str,
        effective_event_type: InventoryEventType,
        since_dt: datetime | None = None,
    ):
        line_column = getattr(InventoryMovement, line_field)

        latest_ids = (
            select(func.max(InventoryMovement.id).label("movement_id"))
            .where(
                InventoryMovement.inventory_id == inventory_id,
                InventoryMovement.is_active == True,  # noqa: E712
                InventoryMovement.source_type == source_type,
                InventoryMovement.value_type == value_type,
                line_column.is_not(None),
            )
            .group_by(line_column)
            .subquery()
        )

        effective = (
            select(
                InventoryMovement.id.label("id"),
                InventoryMovement.quantity.label("quantity"),
                InventoryMovement.unit_value.label("unit_value"),
                InventoryMovement.movement_date.label("movement_date"),
            )
            .join(latest_ids, InventoryMovement.id == latest_ids.c.movement_id)
            .where(InventoryMovement.event_type == effective_event_type)
        )
        if since_dt is not None:
            effective = effective.where(InventoryMovement.movement_date >= since_dt)
        return effective.subquery()

    def get_recent_in_effective_totals(
        self, inventory_id: int, months: int = 12
    ) -> tuple[int, Decimal]:
        since_dt = utcnow() - timedelta(days=30 * months)
        effective = self._effective_line_movements_subquery(
            inventory_id=inventory_id,
            source_type=InventorySourceType.INVOICE,
            value_type=InventoryValueType.COST,
            line_field="invoice_line_id",
            effective_event_type=InventoryEventType.INVOICE_RECEIVED,
            since_dt=since_dt,
        )
        qty_sum, value_sum = (
            self.db.execute(
                select(
                    func.coalesce(func.sum(effective.c.quantity), 0),
                    func.coalesce(
                        func.sum(effective.c.quantity * effective.c.unit_value),
                        Decimal("0"),
                    ),
                )
            ).one()
        )
        return int(qty_sum), value_sum

    def get_latest_in_effective_value(
        self, inventory_id: int, months: int = 12
    ) -> Decimal | None:
        since_dt = utcnow() - timedelta(days=30 * months)
        effective = self._effective_line_movements_subquery(
            inventory_id=inventory_id,
            source_type=InventorySourceType.INVOICE,
            value_type=InventoryValueType.COST,
            line_field="invoice_line_id",
            effective_event_type=InventoryEventType.INVOICE_RECEIVED,
            since_dt=since_dt,
        )
        return self.db.execute(
            select(effective.c.unit_value).order_by(
                effective.c.movement_date.desc(), effective.c.id.desc()
            )
        ).scalars().first()

    def get_recent_out_effective_totals(
        self, inventory_id: int, months: int = 12
    ) -> tuple[int, Decimal]:
        since_dt = utcnow() - timedelta(days=30 * months)
        effective = self._effective_line_movements_subquery(
            inventory_id=inventory_id,
            source_type=InventorySourceType.SALE,
            value_type=InventoryValueType.PRICE,
            line_field="sale_line_id",
            effective_event_type=InventoryEventType.SALE_APPROVED,
            since_dt=since_dt,
        )
        qty_sum, value_sum = (
            self.db.execute(
                select(
                    func.coalesce(func.sum(effective.c.quantity), 0),
                    func.coalesce(
                        func.sum(effective.c.quantity * effective.c.unit_value),
                        Decimal("0"),
                    ),
                )
            ).one()
        )
        return int(qty_sum), value_sum

    def get_latest_out_effective_value(
        self, inventory_id: int, months: int = 12
    ) -> Decimal | None:
        since_dt = utcnow() - timedelta(days=30 * months)
        effective = self._effective_line_movements_subquery(
            inventory_id=inventory_id,
            source_type=InventorySourceType.SALE,
            value_type=InventoryValueType.PRICE,
            line_field="sale_line_id",
            effective_event_type=InventoryEventType.SALE_APPROVED,
            since_dt=since_dt,
        )
        return self.db.execute(
            select(effective.c.unit_value).order_by(
                effective.c.movement_date.desc(), effective.c.id.desc()
            )
        ).scalars().first()
