from __future__ import annotations

from decimal import Decimal
from math import ceil

from fastapi import HTTPException, Response, status
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import select

from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.domain.pdf_generator import PDFGenerator
from src.modules.sale.domain.sale_repository import SaleRepository
from src.modules.sale.sale_schema import (
    SaleCreateWithLines,
    SaleLineCreate,
    SaleLineUpdate,
    SaleReportFilters,
    SaleReportResponse,
    SaleReportRow,
    SaleReportSaleDetail,
    SaleReportSaleLine,
    SaleReportTotals,
    SaleUpdate,
    SaleUpdateStatus,
)
from src.modules.users.domain.users_repository import UserRepository
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.enums.sale_enums import (
    SaleLinePriceType,
    SaleLineQuantityMode,
    SaleStatus,
)
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.utils.datetime import utcnow


def _sqlstate(err: DBAPIError) -> str | None:
    orig = getattr(err, "orig", None)
    return getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)


class SaleService:
    _MONEY_QUANT = Decimal("0.01")

    def __init__(self, repository: SaleRepository) -> None:
        self.repository = repository
        self._pdf_generator = PDFGenerator()

    @staticmethod
    def _money(value: Decimal | int | float | str) -> Decimal:
        return Decimal(str(value)).quantize(SaleService._MONEY_QUANT)

    def _get_sale_or_404(self, sale_id: int) -> Sale:
        sale = self.repository.get(sale_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada.",
            )
        return sale

    def _get_locked_sale_or_404(self, sale_id: int) -> Sale:
        locked = (
            self.repository.db.exec(
                select(Sale.id)
                .where(Sale.id == sale_id, Sale.is_active == True)  # noqa: E712
                .with_for_update()
            ).first()
        )
        if not locked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada.",
            )
        return self._get_sale_or_404(sale_id)

    def _get_line_or_404(self, sale_id: int, line_id: int) -> SaleLine:
        line = self.repository.get_line(sale_id=sale_id, line_id=line_id)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Línea de venta no encontrada.",
            )
        return line

    def _lock_inventory_record(self, inventory_id: int) -> Inventory | None:
        return (
            self.repository.db.exec(
                select(Inventory).where(Inventory.id == inventory_id).with_for_update()
            ).first()
        )

    def _get_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = InventoryRepository(self.repository.db).get(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventario no encontrado.",
            )
        if not inventory.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El inventario inactivo no puede usarse en ventas",
            )
        return inventory

    def _get_locked_active_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = self._lock_inventory_record(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventario no encontrado.",
            )
        if not inventory.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El inventario inactivo no puede usarse en ventas",
            )
        return inventory

    def _get_user_display_name(self, user_id: int | None) -> str | None:
        if not user_id:
            return None
        user = UserRepository(self.repository.db).get(user_id)
        if not user:
            return None
        display_name = " ".join(
            part for part in [user.first_name, user.last_name] if part
        ).strip()
        return display_name or user.email

    def _attach_sale_audit(self, sale: Sale) -> Sale:
        user_repo = UserRepository(self.repository.db)
        set_attr = object.__setattr__

        if sale.created_by:
            user = user_repo.get(sale.created_by)
            set_attr(sale, "created_by_name", self._get_user_display_name(sale.created_by))
            set_attr(sale, "created_by_user", user)
        else:
            set_attr(sale, "created_by_name", None)
            set_attr(sale, "created_by_user", None)

        if sale.updated_by:
            set_attr(sale, "updated_by_name", self._get_user_display_name(sale.updated_by))
        else:
            set_attr(sale, "updated_by_name", None)

        if sale.paid_by:
            user = user_repo.get(sale.paid_by)
            set_attr(sale, "paid_by_name", self._get_user_display_name(sale.paid_by))
            set_attr(sale, "paid_by_user", user)
        else:
            set_attr(sale, "paid_by_name", None)
            set_attr(sale, "paid_by_user", None)

        if sale.cancelled_by:
            user = user_repo.get(sale.cancelled_by)
            set_attr(
                sale,
                "cancelled_by_name",
                self._get_user_display_name(sale.cancelled_by),
            )
            set_attr(sale, "cancelled_by_user", user)
        else:
            set_attr(sale, "cancelled_by_name", None)
            set_attr(sale, "cancelled_by_user", None)

        for line in sale.lines:
            self._attach_line_projection(line)

        return sale

    def _available_boxes(self, inventory: Inventory) -> int:
        return int(inventory.stock - inventory.reserved_stock)

    def _get_existing_unit_inventory(
        self,
        *,
        source_inventory: Inventory,
        lock: bool = False,
    ) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.warehouse_id == source_inventory.warehouse_id,
            Inventory.product_id == source_inventory.product_id,
            Inventory.box_size == 1,
        )
        if lock:
            stmt = stmt.with_for_update()
        return self.repository.db.exec(stmt).first()

    def _get_piece_inventory_or_404(
        self,
        *,
        source_inventory: Inventory,
        create_if_missing: bool,
    ) -> Inventory:
        if int(source_inventory.box_size or 1) <= 1:
            return source_inventory
        if create_if_missing:
            return self._ensure_unit_inventory(source_inventory=source_inventory)
        existing = self._get_existing_unit_inventory(source_inventory=source_inventory, lock=True)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se encontró el inventario unitario del producto.",
            )
        if not existing.is_active:
            existing.is_active = True
        return existing

    def _piece_projection(
        self,
        *,
        source_inventory: Inventory,
        requested_units: int,
        current_line_reserved_units: int = 0,
    ) -> dict[str, int | None]:
        if int(source_inventory.box_size or 1) <= 1:
            available_units = max(
                int(source_inventory.stock)
                - max(int(source_inventory.reserved_stock) - current_line_reserved_units, 0),
                0,
            )
            return {
                "source_box_size": int(source_inventory.box_size or 1),
                "projected_units_from_stock": min(int(requested_units), available_units),
                "projected_boxes_to_open": 0,
                "projected_units_leftover": 0,
            }

        unit_inventory = self._get_existing_unit_inventory(
            source_inventory=source_inventory,
            lock=False,
        )
        unit_stock = int(unit_inventory.stock) if unit_inventory else 0
        unit_reserved = int(unit_inventory.reserved_stock) if unit_inventory else 0
        available_units = max(unit_stock - max(unit_reserved - current_line_reserved_units, 0), 0)
        units_from_stock = min(int(requested_units), available_units)
        remaining_units = max(int(requested_units) - units_from_stock, 0)
        box_size = max(int(source_inventory.box_size or 1), 1)
        boxes_to_open = ceil(remaining_units / box_size) if remaining_units > 0 else 0
        units_leftover = (boxes_to_open * box_size - remaining_units) if boxes_to_open > 0 else 0
        return {
            "source_box_size": box_size,
            "projected_units_from_stock": units_from_stock,
            "projected_boxes_to_open": boxes_to_open,
            "projected_units_leftover": units_leftover,
        }

    def _attach_line_projection(self, line: SaleLine) -> SaleLine:
        set_attr = object.__setattr__
        inventory = line.inventory
        if inventory is None:
            try:
                inventory = self._get_inventory_or_404(line.inventory_id)
            except HTTPException:
                inventory = None

        if inventory is None or line.quantity_mode != SaleLineQuantityMode.UNIT:
            set_attr(line, "source_box_size", None)
            set_attr(line, "projected_units_from_stock", None)
            set_attr(line, "projected_boxes_to_open", None)
            set_attr(line, "projected_units_leftover", None)
            return line

        current_line_reserved_units = int(line.quantity_units) if line.reservation_applied else 0
        projection = self._piece_projection(
            source_inventory=inventory,
            requested_units=int(line.quantity_units),
            current_line_reserved_units=current_line_reserved_units,
        )
        set_attr(line, "source_box_size", projection["source_box_size"])
        set_attr(line, "projected_units_from_stock", projection["projected_units_from_stock"])
        set_attr(line, "projected_boxes_to_open", projection["projected_boxes_to_open"])
        set_attr(line, "projected_units_leftover", projection["projected_units_leftover"])
        return line

    def _ensure_physical_stock_available(
        self, inventory: Inventory, quantity: int, *, operation: str
    ) -> None:
        if int(inventory.stock) < int(quantity):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No hay stock físico suficiente para {operation}.",
            )

    def _normalize_sale_price(
        self,
        *,
        price: Decimal,
        price_type: SaleLinePriceType,
        box_size: int,
    ) -> tuple[Decimal, Decimal]:
        box_size = max(int(box_size or 1), 1)
        if price_type == SaleLinePriceType.UNIT:
            unit_price = self._money(price)
            box_price = self._money(unit_price * Decimal(box_size))
        else:
            box_price = self._money(price)
            unit_price = self._money(box_price / Decimal(box_size))
        return unit_price, box_price

    def _effective_request_quantity_and_mode(
        self,
        *,
        inventory: Inventory,
        price_type: SaleLinePriceType,
        quantity_boxes: int | None,
        quantity_units: int | None,
    ) -> tuple[int, SaleLineQuantityMode]:
        if quantity_boxes is not None:
            return int(quantity_boxes), SaleLineQuantityMode.BOX
        if quantity_units is not None:
            if int(inventory.box_size or 1) > 1 and price_type == SaleLinePriceType.UNIT:
                return int(quantity_units), SaleLineQuantityMode.UNIT
            return int(quantity_units), SaleLineQuantityMode.BOX
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe enviarse quantity_boxes o quantity_units.",
        )

    def _preview_effective_inventory_key(
        self, inventory: Inventory, quantity_mode: SaleLineQuantityMode
    ) -> tuple[int | str, int | None, int | None]:
        if quantity_mode == SaleLineQuantityMode.UNIT:
            return ("UNIT", inventory.warehouse_id, inventory.product_id)
        return (inventory.id, None, None)

    def _existing_line_effective_key(self, line: SaleLine) -> tuple[int | str, int | None, int | None]:
        inventory = line.inventory
        if inventory and line.quantity_mode == SaleLineQuantityMode.UNIT:
            return ("UNIT", inventory.warehouse_id, inventory.product_id)
        return (line.inventory_id, None, None)

    def _ensure_no_duplicate_effective_inventory(
        self,
        sale: Sale,
        key: tuple[int | str, int | None, int | None],
        *,
        current_line_id: int | None = None,
    ) -> None:
        for existing in sale.lines:
            if not existing.is_active:
                continue
            if current_line_id is not None and existing.id == current_line_id:
                continue
            if self._existing_line_effective_key(existing) == key:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se permite repetir el mismo inventario efectivo en las líneas de venta.",
                )

    def _apply_line_snapshot(
        self,
        line: SaleLine,
        *,
        inventory: Inventory,
        quantity: int,
        price: Decimal,
        price_type: SaleLinePriceType,
        quantity_mode: SaleLineQuantityMode,
    ) -> None:
        snapshot_box_size = (
            1
            if quantity_mode == SaleLineQuantityMode.UNIT and int(inventory.box_size or 1) > 1
            else int(inventory.box_size or 1)
        )
        unit_price, box_price = self._normalize_sale_price(
            price=price,
            price_type=price_type,
            box_size=snapshot_box_size,
        )
        product = inventory.product
        line.quantity_units = int(quantity)
        line.box_size = snapshot_box_size
        line.price = box_price
        line.price_type = price_type
        line.quantity_mode = quantity_mode
        line.unit_price = unit_price
        line.box_price = box_price
        total_unit = unit_price if quantity_mode == SaleLineQuantityMode.UNIT else box_price
        line.total_price = self._money(Decimal(quantity) * total_unit)
        line.product_code = product.code if product else None
        line.product_name = product.name if product else None

    def _line_total(self, line: SaleLine) -> Decimal:
        return line.total_price

    def _recalculate_sale_total(self, sale: Sale) -> None:
        total = Decimal("0.00")
        for line in sale.lines:
            if line.is_active:
                total += self._line_total(line)
        sale.total_price = total

    def _sale_line_quantity_boxes(self, line: SaleLine) -> int:
        return int(getattr(line, "quantity_boxes", line.quantity_units))

    def _sale_line_inventory_quantity(self, line: SaleLine) -> int:
        return int(line.quantity_units)

    def _ensure_piece_stock_available(
        self,
        source_inventory: Inventory,
        requested_units: int,
        *,
        operation: str,
    ) -> None:
        box_size = max(int(source_inventory.box_size or 1), 1)
        unit_inventory = self._get_existing_unit_inventory(
            source_inventory=source_inventory,
            lock=False,
        )
        unit_stock = int(unit_inventory.stock) if unit_inventory else 0
        total_available_units = unit_stock + (int(source_inventory.stock) * box_size)
        if total_available_units < int(requested_units):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No hay stock físico suficiente para {operation}.",
            )

    def _release_line_reservation(
        self,
        *,
        line: SaleLine,
        inventory: Inventory,
        movement_repository: InventoryMovementRepository,
        movement_group_id: str,
        movement_sequence: int,
    ) -> int:
        quantity = self._sale_line_inventory_quantity(line)
        inventory.reserved_stock = max(int(inventory.reserved_stock) - quantity, 0)
        movement_repository.add(
            InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.SALE,
                event_type=InventoryEventType.SALE_RELEASED,
                movement_type=InventoryMovementType.IN_,
                value_type=InventoryValueType.PRICE,
                quantity=quantity,
                unit_value=(
                    line.unit_price
                    if line.quantity_mode == SaleLineQuantityMode.UNIT
                    else line.price
                ),
                prev_stock=inventory.stock,
                new_stock=inventory.stock,
                inventory_id=inventory.id,
                sale_line_id=line.id,
            ),
            commit=False,
        )
        line.reservation_applied = False
        return movement_sequence + 1

    def _ensure_unit_inventory(
        self,
        *,
        source_inventory: Inventory,
    ) -> Inventory:
        inventory_repo = InventoryRepository(self.repository.db)
        existing = (
            self.repository.db.exec(
                select(Inventory)
                .where(
                    Inventory.warehouse_id == source_inventory.warehouse_id,
                    Inventory.product_id == source_inventory.product_id,
                    Inventory.box_size == 1,
                )
                .with_for_update()
            ).first()
        )
        if existing is not None:
            if not existing.is_active:
                existing.is_active = True
            return existing

        unit_cost = self._money(
            (source_inventory.last_cost or Decimal("0.00"))
            / Decimal(max(int(source_inventory.box_size or 1), 1))
        )
        unit_inventory = Inventory(
            stock=0,
            reserved_stock=0,
            box_size=1,
            avg_cost=unit_cost,
            last_cost=unit_cost,
            warehouse_id=source_inventory.warehouse_id,
            product_id=source_inventory.product_id,
            is_active=True,
        )
        inventory_repo.add(unit_inventory, commit=False)
        self.repository.db.flush()
        return unit_inventory

    def _open_boxes_for_piece_sale(
        self,
        *,
        line: SaleLine,
        source_inventory: Inventory,
        requested_units: int,
        movement_repository: InventoryMovementRepository,
        movement_group_id: str,
        movement_sequence: int,
    ) -> tuple[Inventory, int]:
        unit_inventory = self._ensure_unit_inventory(source_inventory=source_inventory)
        if unit_inventory.stock >= requested_units:
            return unit_inventory, movement_sequence

        units_deficit = requested_units - int(unit_inventory.stock)
        box_size = max(int(source_inventory.box_size or 1), 1)
        boxes_to_open = ceil(units_deficit / box_size)
        self._ensure_physical_stock_available(
            source_inventory,
            boxes_to_open,
            operation="abrir cajas para venta por pieza",
        )

        opened_units = boxes_to_open * box_size
        source_prev_stock = source_inventory.stock
        source_inventory.stock = source_prev_stock - boxes_to_open

        source_unit_cost = self._money(
            (source_inventory.last_cost or Decimal("0.00")) / Decimal(box_size)
        )
        unit_prev_stock = unit_inventory.stock
        unit_inventory.stock = unit_prev_stock + opened_units
        if unit_inventory.stock > 0:
            previous_total = Decimal(unit_prev_stock) * unit_inventory.avg_cost
            added_total = Decimal(opened_units) * source_unit_cost
            unit_inventory.avg_cost = self._money(
                (previous_total + added_total) / Decimal(unit_inventory.stock)
            )
        unit_inventory.last_cost = source_unit_cost

        movement_repository.add(
            InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.SALE,
                event_type=InventoryEventType.BOX_OPENED_OUT,
                movement_type=InventoryMovementType.OUT,
                value_type=InventoryValueType.COST,
                quantity=boxes_to_open,
                unit_value=source_inventory.last_cost,
                prev_stock=source_prev_stock,
                new_stock=source_inventory.stock,
                inventory_id=source_inventory.id,
                sale_line_id=line.id,
            ),
            commit=False,
        )
        movement_sequence += 1
        movement_repository.add(
            InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.SALE,
                event_type=InventoryEventType.BOX_OPENED_IN,
                movement_type=InventoryMovementType.IN_,
                value_type=InventoryValueType.COST,
                quantity=opened_units,
                unit_value=source_unit_cost,
                prev_stock=unit_prev_stock,
                new_stock=unit_inventory.stock,
                inventory_id=unit_inventory.id,
                sale_line_id=line.id,
            ),
            commit=False,
        )
        movement_sequence += 1
        return unit_inventory, movement_sequence

    def _ensure_sale_can_be_paid(self, sale: Sale) -> None:
        for line in sale.lines:
            if not line.is_active:
                continue
            if line.price <= Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede marcar la venta como pagada con líneas de precio cero.",
                )

    def _apply_sale_reserved(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)
        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        for line in sale.lines:
            if not line.is_active or line.reservation_applied:
                continue

            source_inventory = self._get_locked_active_inventory_or_404(line.inventory_id)
            self._apply_line_snapshot(
                line,
                inventory=source_inventory,
                quantity=line.quantity_units,
                price=(
                    line.unit_price
                    if line.price_type == SaleLinePriceType.UNIT
                    else line.price
                ),
                price_type=line.price_type,
                quantity_mode=line.quantity_mode,
            )
            reservation_inventory = source_inventory
            quantity = self._sale_line_inventory_quantity(line)

            if line.quantity_mode == SaleLineQuantityMode.UNIT and int(source_inventory.box_size or 1) > 1:
                self._ensure_piece_stock_available(
                    source_inventory,
                    quantity,
                    operation="apartar inventario",
                )
                reservation_inventory = self._ensure_unit_inventory(
                    source_inventory=source_inventory
                )
            else:
                self._ensure_physical_stock_available(
                    source_inventory,
                    quantity,
                    operation="apartar inventario",
                )

            reservation_inventory.reserved_stock += quantity
            movement_repository.add(
                InventoryMovement(
                    movement_group_id=movement_group_id,
                    movement_sequence=movement_sequence,
                    source_type=InventorySourceType.SALE,
                    event_type=InventoryEventType.SALE_RESERVED,
                    movement_type=InventoryMovementType.OUT,
                    value_type=InventoryValueType.PRICE,
                    quantity=quantity,
                    unit_value=(
                        line.unit_price
                        if line.quantity_mode == SaleLineQuantityMode.UNIT
                        else line.price
                    ),
                    prev_stock=reservation_inventory.stock,
                    new_stock=reservation_inventory.stock,
                    inventory_id=reservation_inventory.id,
                    sale_line_id=line.id,
                ),
                commit=False,
            )
            movement_sequence += 1
            line.reservation_applied = True
            inventory_repository.update(reservation_inventory, commit=False)
            session.add(line)

    def _apply_sale_release(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)
        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        for line in sale.lines:
            if not line.is_active or not line.reservation_applied:
                continue

            source_inventory = self._get_locked_active_inventory_or_404(line.inventory_id)
            reservation_inventory = (
                self._get_piece_inventory_or_404(
                    source_inventory=source_inventory,
                    create_if_missing=False,
                )
                if line.quantity_mode == SaleLineQuantityMode.UNIT
                else source_inventory
            )
            movement_sequence = self._release_line_reservation(
                line=line,
                inventory=reservation_inventory,
                movement_repository=movement_repository,
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
            )
            inventory_repository.update(reservation_inventory, commit=False)
            session.add(line)

    def _apply_sale_paid(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)
        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        for line in sale.lines:
            if not line.is_active or line.inventory_applied:
                continue

            source_inventory = self._get_locked_active_inventory_or_404(line.inventory_id)
            self._apply_line_snapshot(
                line,
                inventory=source_inventory,
                quantity=line.quantity_units,
                price=(
                    line.unit_price
                    if line.price_type == SaleLinePriceType.UNIT
                    else line.price
                ),
                price_type=line.price_type,
                quantity_mode=line.quantity_mode,
            )
            quantity = self._sale_line_inventory_quantity(line)
            inventory = source_inventory

            if line.quantity_mode == SaleLineQuantityMode.UNIT and int(source_inventory.box_size or 1) > 1:
                inventory = self._ensure_unit_inventory(source_inventory=source_inventory)
                if line.reservation_applied:
                    movement_sequence = self._release_line_reservation(
                        line=line,
                        inventory=inventory,
                        movement_repository=movement_repository,
                        movement_group_id=movement_group_id,
                        movement_sequence=movement_sequence,
                    )
                self._ensure_piece_stock_available(
                    source_inventory,
                    quantity,
                    operation="aplicar la venta por pieza",
                )
                inventory, movement_sequence = self._open_boxes_for_piece_sale(
                    line=line,
                    source_inventory=source_inventory,
                    requested_units=quantity,
                    movement_repository=movement_repository,
                    movement_group_id=movement_group_id,
                    movement_sequence=movement_sequence,
                )
            elif line.reservation_applied:
                movement_sequence = self._release_line_reservation(
                    line=line,
                    inventory=inventory,
                    movement_repository=movement_repository,
                    movement_group_id=movement_group_id,
                    movement_sequence=movement_sequence,
                )

            prev_stock = inventory.stock
            new_stock = prev_stock - quantity
            if new_stock < 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El inventario no puede quedar en negativo",
                )

            inventory.stock = new_stock
            movement_repository.add(
                InventoryMovement(
                    movement_group_id=movement_group_id,
                    movement_sequence=movement_sequence,
                    source_type=InventorySourceType.SALE,
                    event_type=InventoryEventType.SALE_APPROVED,
                    movement_type=InventoryMovementType.OUT,
                    value_type=InventoryValueType.PRICE,
                    quantity=quantity,
                    unit_value=(
                        line.unit_price
                        if line.quantity_mode == SaleLineQuantityMode.UNIT
                        else line.price
                    ),
                    prev_stock=prev_stock,
                    new_stock=new_stock,
                    inventory_id=inventory.id,
                    sale_line_id=line.id,
                ),
                commit=False,
            )
            movement_sequence += 1
            line.inventory_applied = True
            inventory_repository.update(inventory, commit=False)
            session.add(line)

    def _apply_sale_unpaid(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)
        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        for line in sale.lines:
            if not line.is_active or not line.inventory_applied:
                continue

            source_inventory = self._get_locked_active_inventory_or_404(line.inventory_id)
            inventory = (
                self._ensure_unit_inventory(source_inventory=source_inventory)
                if line.quantity_mode == SaleLineQuantityMode.UNIT
                and int(source_inventory.box_size or 1) > 1
                else source_inventory
            )
            quantity = self._sale_line_inventory_quantity(line)
            prev_stock = inventory.stock
            inventory.stock = prev_stock + quantity
            movement_repository.add(
                InventoryMovement(
                    movement_group_id=movement_group_id,
                    movement_sequence=movement_sequence,
                    source_type=InventorySourceType.SALE,
                    event_type=InventoryEventType.SALE_REVERSED,
                    movement_type=InventoryMovementType.IN_,
                    value_type=InventoryValueType.PRICE,
                    quantity=quantity,
                    unit_value=(
                        line.unit_price
                        if line.quantity_mode == SaleLineQuantityMode.UNIT
                        else line.price
                    ),
                    prev_stock=prev_stock,
                    new_stock=inventory.stock,
                    inventory_id=inventory.id,
                    sale_line_id=line.id,
                ),
                commit=False,
            )
            movement_sequence += 1
            line.inventory_applied = False
            inventory_repository.update(inventory, commit=False)
            session.add(line)

    def _apply_sale_state_delta(self, sale: Sale, mutator) -> None:
        if sale.status == SaleStatus.PAID:
            self._apply_sale_unpaid(sale)
        elif sale.status == SaleStatus.DRAFT:
            self._apply_sale_release(sale)

        mutator()
        self._recalculate_sale_total(sale)

        if sale.status == SaleStatus.PAID:
            self._ensure_sale_can_be_paid(sale)
            self._apply_sale_paid(sale)
        elif sale.status == SaleStatus.DRAFT:
            self._apply_sale_reserved(sale)

    def list_sales(self, skip: int = 0, limit: int | None = None):
        return [self._attach_sale_audit(sale) for sale in self.repository.list(skip=skip, limit=limit)]

    def get_sale(self, sale_id: int):
        return self._attach_sale_audit(self._get_sale_or_404(sale_id))

    def create_sale(self, payload: SaleCreateWithLines, current_user=None) -> Sale:
        if payload.status != SaleStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La venta solo se puede crear en estado DRAFT.",
            )

        sale = Sale(
            sale_date=payload.sale_date,
            status=payload.status,
            notes=payload.notes,
            client_id=payload.client_id,
            created_by=getattr(current_user, "id", None),
            updated_by=getattr(current_user, "id", None),
        )

        seen_keys: set[tuple[int | str, int | None, int | None]] = set()
        session = self.repository.db

        try:
            for payload_line in payload.lines:
                inventory = self._get_inventory_or_404(payload_line.inventory_id)
                quantity, quantity_mode = self._effective_request_quantity_and_mode(
                    inventory=inventory,
                    price_type=payload_line.price_type,
                    quantity_boxes=payload_line.quantity_boxes,
                    quantity_units=payload_line.quantity_units,
                )
                if quantity_mode == SaleLineQuantityMode.UNIT and int(inventory.box_size or 1) > 1:
                    self._ensure_piece_stock_available(
                        inventory,
                        quantity,
                        operation="registrar la venta",
                    )
                else:
                    self._ensure_physical_stock_available(
                        inventory,
                        quantity,
                        operation="registrar la venta",
                    )
                key = self._preview_effective_inventory_key(inventory, quantity_mode)
                if key in seen_keys:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="No se permite repetir el mismo inventario efectivo en las líneas de venta.",
                    )
                seen_keys.add(key)
                sale.lines.append(
                    SaleLine(
                        inventory_id=inventory.id,
                        quantity_units=quantity,
                        box_size=inventory.box_size,
                        price=self._money(payload_line.price),
                        price_type=payload_line.price_type,
                        quantity_mode=quantity_mode,
                        unit_price=self._money(payload_line.price)
                        if payload_line.price_type == SaleLinePriceType.UNIT
                        else Decimal("0.00"),
                        box_price=Decimal("0.00"),
                        total_price=Decimal("0.00"),
                        product_code=inventory.product.code if inventory.product else None,
                        product_name=inventory.product.name if inventory.product else None,
                    )
                )

            session.add(sale)
            session.flush()
            self._apply_sale_reserved(sale)
            self._recalculate_sale_total(sale)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Referencia inválida a cliente o inventario.",
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise

        return self._attach_sale_audit(
            self.repository.get(sale.id, include_inactive=True)  # type: ignore[arg-type]
        )

    def update_sale(self, sale_id: int, payload: SaleUpdate, current_user=None) -> Sale:
        sale = self._get_sale_or_404(sale_id)

        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(sale, field, value)
        if current_user is not None:
            sale.updated_by = getattr(current_user, "id", None)

        try:
            self.repository.update(sale)
        except IntegrityError:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Referencia inválida a cliente.",
            )

        return self._attach_sale_audit(self._get_sale_or_404(sale_id))

    def update_sale_status(
        self, sale_id: int, payload: SaleUpdateStatus, current_user=None
    ) -> Sale:
        session = self.repository.db

        try:
            sale = self._get_locked_sale_or_404(sale_id)
            previous_status = sale.status
            new_status = payload.status

            if previous_status == new_status:
                session.commit()
                return self._attach_sale_audit(sale)

            allowed_transitions = {
                SaleStatus.DRAFT: {SaleStatus.PAID, SaleStatus.CANCELLED},
                SaleStatus.PAID: {SaleStatus.DRAFT, SaleStatus.CANCELLED},
                SaleStatus.CANCELLED: {SaleStatus.DRAFT},
            }
            if new_status not in allowed_transitions.get(previous_status, set()):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La transición de estado no es válida.",
                )

            if new_status == SaleStatus.PAID:
                self._ensure_sale_can_be_paid(sale)
                self._apply_sale_paid(sale)
                sale.paid_by = getattr(current_user, "id", None)
                sale.paid_at = utcnow()
            elif new_status == SaleStatus.CANCELLED:
                if previous_status == SaleStatus.DRAFT:
                    self._apply_sale_release(sale)
                elif previous_status == SaleStatus.PAID:
                    self._apply_sale_unpaid(sale)
                sale.cancelled_by = getattr(current_user, "id", None)
                sale.cancelled_at = utcnow()
            elif new_status == SaleStatus.DRAFT:
                if previous_status == SaleStatus.PAID:
                    self._apply_sale_unpaid(sale)
                self._apply_sale_reserved(sale)

            sale.status = new_status
            if current_user is not None:
                sale.updated_by = getattr(current_user, "id", None)
            session.add(sale)
            self._recalculate_sale_total(sale)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            state = _sqlstate(e)
            if state in {"22P02", "23514"} and "PAID" in str(getattr(e, "orig", e)):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "La base de datos no acepta sale.status='PAID'. "
                        "Ejecuta la migración puntual para normalizar estados."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo actualizar el estado de la venta.",
            )
        except HTTPException:
            session.rollback()
            raise
        except DBAPIError as e:
            session.rollback()
            state = _sqlstate(e)
            if state in {"22P02", "23514"} and "PAID" in str(getattr(e, "orig", e)):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "La base de datos no acepta sale.status='PAID'. "
                        "Ejecuta la migración puntual para normalizar estados."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de base de datos al actualizar el estado de la venta.",
            )
        except Exception:
            session.rollback()
            raise

        return self._attach_sale_audit(self._get_sale_or_404(sale_id))

    def delete_sale(self, sale_id: int) -> Sale:
        session = self.repository.db
        sale = self._get_locked_sale_or_404(sale_id)
        if sale.status == SaleStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar una venta PAID. Primero regresa el estado.",
            )
        try:
            if sale.status == SaleStatus.DRAFT:
                self._apply_sale_release(sale)
            self.repository.soft_delete(sale, commit=False)
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise
        return self._attach_sale_audit(
            self.repository.get(sale_id, include_inactive=True)  # type: ignore[arg-type]
        )

    def add_sale_line(self, sale_id: int, payload: SaleLineCreate, current_user=None) -> SaleLine:
        session = self.repository.db
        sale = self._get_locked_sale_or_404(sale_id)
        created_line: SaleLine | None = None

        try:
            inventory = self._get_inventory_or_404(payload.inventory_id)
            quantity, quantity_mode = self._effective_request_quantity_and_mode(
                inventory=inventory,
                price_type=payload.price_type,
                quantity_boxes=payload.quantity_boxes,
                quantity_units=payload.quantity_units,
            )
            key = self._preview_effective_inventory_key(inventory, quantity_mode)
            self._ensure_no_duplicate_effective_inventory(sale, key)

            def mutate() -> SaleLine:
                nonlocal created_line
                created_line = self.repository.add_line(
                    sale,
                    SaleLine(
                        inventory_id=inventory.id,
                        quantity_units=quantity,
                        box_size=inventory.box_size,
                        price=self._money(payload.price),
                        price_type=payload.price_type,
                        quantity_mode=quantity_mode,
                        unit_price=self._money(payload.price)
                        if payload.price_type == SaleLinePriceType.UNIT
                        else Decimal("0.00"),
                        box_price=Decimal("0.00"),
                        total_price=Decimal("0.00"),
                        product_code=inventory.product.code if inventory.product else None,
                        product_name=inventory.product.name if inventory.product else None,
                    ),
                    commit=False,
                )
                return created_line

            self._apply_sale_state_delta(sale, mutate)
            if current_user is not None:
                sale.updated_by = getattr(current_user, "id", None)
            self.repository.update(sale, commit=False)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Referencia inválida a inventario.",
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise

        if created_line is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo crear la línea de venta.",
            )
        return self.repository.get_line(sale.id, created_line.id) or created_line

    def update_sale_line(
        self, sale_id: int, line_id: int, payload: SaleLineUpdate, current_user=None
    ) -> SaleLine:
        session = self.repository.db
        sale = self._get_locked_sale_or_404(sale_id)
        line = self._get_line_or_404(sale_id, line_id)

        try:
            data = payload.model_dump(exclude_unset=True)
            preview_inventory = (
                self._get_inventory_or_404(data["inventory_id"])
                if "inventory_id" in data
                else self._get_inventory_or_404(line.inventory_id)
            )
            next_price_type = data.get("price_type", line.price_type)
            if "quantity_boxes" in data or "quantity_units" in data:
                quantity, quantity_mode = self._effective_request_quantity_and_mode(
                    inventory=preview_inventory,
                    price_type=next_price_type,
                    quantity_boxes=data.get("quantity_boxes"),
                    quantity_units=data.get("quantity_units"),
                )
            else:
                quantity = line.quantity_units
                quantity_mode = line.quantity_mode
            key = self._preview_effective_inventory_key(preview_inventory, quantity_mode)
            self._ensure_no_duplicate_effective_inventory(
                sale,
                key,
                current_line_id=line.id,
            )

            def mutate() -> None:
                line.inventory_id = preview_inventory.id
                line.quantity_units = quantity
                line.price_type = next_price_type
                line.quantity_mode = quantity_mode
                if "price" in data:
                    line.price = self._money(data["price"])
                self.repository.update_line(line, commit=False)

            self._apply_sale_state_delta(sale, mutate)
            if current_user is not None:
                sale.updated_by = getattr(current_user, "id", None)
            self.repository.update(sale, commit=False)
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Referencia inválida a inventario.",
            )
        except Exception:
            session.rollback()
            raise

        return self.repository.get_line(sale_id, line_id) or line

    def delete_sale_line(self, sale_id: int, line_id: int, current_user=None) -> SaleLine:
        session = self.repository.db
        sale = self._get_locked_sale_or_404(sale_id)
        line = self._get_line_or_404(sale_id, line_id)

        try:
            def mutate() -> None:
                self.repository.soft_delete_line(line, commit=False)

            self._apply_sale_state_delta(sale, mutate)
            if current_user is not None:
                sale.updated_by = getattr(current_user, "id", None)
            self.repository.update(sale, commit=False)
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise

        return line

    def get_sales_report(self, filters: SaleReportFilters) -> SaleReportResponse:
        lines = self.repository.list_lines_for_report(
            from_date=filters.from_date,
            to_date=filters.to_date,
            status=filters.status,
            client_id=filters.client_id,
            product_id=filters.product_id,
            warehouse_id=filters.warehouse_id,
            inventory_id=filters.inventory_id,
        )

        totals_boxes = 0
        totals_amount = Decimal("0.00")
        sale_ids = set()

        sales_map: dict[int, SaleReportSaleDetail] = {}
        for line in lines:
            sale = line.sale
            if not sale:
                continue

            sale_ids.add(sale.id)
            totals_boxes += self._sale_line_quantity_boxes(line)
            totals_amount += line.total_price

            if sale.id not in sales_map:
                sales_map[sale.id] = SaleReportSaleDetail(
                    id=sale.id,
                    sale_date=sale.sale_date,
                    status=sale.status,
                    client=sale.client,
                    total_amount=Decimal("0.00"),
                    created_by=sale.created_by,
                    updated_by=sale.updated_by,
                    paid_by=sale.paid_by,
                    cancelled_by=sale.cancelled_by,
                    created_by_name=self._get_user_display_name(sale.created_by),
                    updated_by_name=self._get_user_display_name(sale.updated_by),
                    paid_by_name=self._get_user_display_name(sale.paid_by),
                    cancelled_by_name=self._get_user_display_name(sale.cancelled_by),
                    lines=[],
                )

            sales_map[sale.id].lines.append(
                SaleReportSaleLine(
                    id=line.id,
                    inventory_id=line.inventory_id,
                    quantity_boxes=self._sale_line_quantity_boxes(line),
                    box_size=int(
                        getattr(line, "box_size", None)
                        or (line.inventory.box_size if line.inventory else 1)
                    ),
                    price=line.price,
                    price_type=line.price_type,
                    unit_price=line.unit_price,
                    box_price=line.box_price,
                    total_price=line.total_price,
                    product_code=getattr(line, "product_code", None),
                    product_name=getattr(line, "product_name", None),
                    inventory=line.inventory,
                )
            )
            sales_map[sale.id].total_amount += line.total_price

        rows: list[SaleReportRow] = []
        if filters.group_by:
            grouped: dict[tuple[int, str], dict[str, Decimal | int]] = {}
            for line in lines:
                inventory = line.inventory
                sale = line.sale
                if not inventory or not sale:
                    continue

                if filters.group_by == "product":
                    group_id = inventory.product_id
                    group_label = (
                        inventory.product.name if inventory.product else str(group_id)
                    )
                elif filters.group_by == "warehouse":
                    group_id = inventory.warehouse_id
                    group_label = (
                        inventory.warehouse.name
                        if inventory.warehouse
                        else str(group_id)
                    )
                elif filters.group_by == "client":
                    group_id = sale.client_id
                    group_label = sale.client.name if sale.client else str(group_id)
                else:
                    group_id = inventory.id
                    group_label = str(group_id)

                key = (group_id, group_label)
                if key not in grouped:
                    grouped[key] = {"units": 0, "amount": Decimal("0.00")}
                grouped[key]["units"] = int(grouped[key]["units"]) + self._sale_line_quantity_boxes(line)
                grouped[key]["amount"] = Decimal(grouped[key]["amount"]) + line.total_price

            for (group_id, group_label), data in grouped.items():
                rows.append(
                    SaleReportRow(
                        group_by=filters.group_by,
                        group_id=group_id,
                        group_label=group_label,
                        total_boxes=int(data["units"]),
                        total_amount=Decimal(data["amount"]),
                    )
                )

        return SaleReportResponse(
            period={"from_date": filters.from_date, "to_date": filters.to_date},
            filters={
                "status": filters.status,
                "client_id": filters.client_id,
                "product_id": filters.product_id,
                "warehouse_id": filters.warehouse_id,
                "inventory_id": filters.inventory_id,
                "group_by": filters.group_by,
            },
            totals=SaleReportTotals(
                sales_count=len(sale_ids),
                total_boxes=totals_boxes,
                total_amount=totals_amount,
            ),
            rows=rows,
            sales=list(sales_map.values()),
        )

    def generate_invoice_pdf(self, sale_id: int):
        sale = self._get_sale_or_404(sale_id)
        delivered_by_name = self._get_user_display_name(
            getattr(sale, "paid_by", None) or getattr(sale, "updated_by", None)
        )
        pdf_bytes = self._pdf_generator.generate_sale_invoice_pdf(
            sale,
            delivered_by_name=delivered_by_name,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="factura_{sale_id}.pdf"'},
        )
