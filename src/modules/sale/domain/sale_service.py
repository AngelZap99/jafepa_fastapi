from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status, Response
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import select

from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.enums.sale_enums import SaleLinePriceType, SaleStatus
from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.modules.inventory.domain.pdf_generator import PDFGenerator
from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.sale.domain.sale_repository import SaleRepository
from src.modules.users.domain.users_repository import UserRepository
from src.modules.sale.sale_schema import (
    SaleCreateWithLines,
    SaleLineCreate,
    SaleLineUpdate,
    SaleUpdate,
    SaleUpdateStatus,
    SaleReportFilters,
    SaleReportResponse,
    SaleReportTotals,
    SaleReportRow,
    SaleReportSaleDetail,
    SaleReportSaleLine,
)


def _sqlstate(err: DBAPIError) -> str | None:
    # Tries common psycopg/psycopg2 attributes
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found"
            )
        return sale

    def _get_line_or_404(self, sale_id: int, line_id: int) -> SaleLine:
        line = self.repository.get_line(sale_id=sale_id, line_id=line_id)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sale line not found"
            )
        return line

    def _get_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = InventoryRepository(self.repository.db).get(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory record not found",
            )
        if not inventory.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Inactive inventory cannot be used in sales",
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

    def _available_boxes(self, inventory: Inventory) -> int:
        return int(inventory.stock)

    def _ensure_stock_available(self, inventory: Inventory, quantity_boxes: int) -> None:
        if self._available_boxes(inventory) < quantity_boxes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient stock in boxes for sale line",
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

    def _line_total(self, line: SaleLine) -> Decimal:
        quantity_boxes = self._sale_line_quantity_boxes(line)
        return Decimal(quantity_boxes) * line.price

    def _line_snapshot_values(
        self,
        inventory: Inventory,
        *,
        quantity_boxes: int,
        price: Decimal,
        price_type: SaleLinePriceType,
    ) -> dict[str, object]:
        box_size = int(inventory.box_size or 1)
        unit_price, box_price = self._normalize_sale_price(
            price=price,
            price_type=price_type,
            box_size=box_size,
        )
        product = inventory.product
        return {
            "quantity_units": quantity_boxes,
            "box_size": box_size,
            "price_type": price_type,
            "price": box_price,
            "unit_price": unit_price,
            "box_price": box_price,
            "total_price": self._money(Decimal(quantity_boxes) * box_price),
            "product_code": product.code if product else None,
            "product_name": product.name if product else None,
        }

    def _recalculate_sale_total(self, sale: Sale) -> None:
        total = Decimal("0.00")
        for line in sale.lines:
            if line.is_active:
                total += line.total_price
        sale.total_price = total

    def _sale_line_quantity_boxes(self, line: SaleLine) -> int:
        return int(getattr(line, "quantity_boxes", line.quantity_units))

    def _apply_paid_sale_delta(self, sale: Sale, mutator) -> None:
        paid = sale.status == SaleStatus.PAID
        if paid:
            self._apply_sale_unpaid(sale)

        mutator()
        self._recalculate_sale_total(sale)

        if paid:
            self._apply_sale_paid(sale)

    def _apply_sale_paid(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)

        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        inventory_ids = [
            line.inventory_id
            for line in sale.lines
            if line.is_active and not line.inventory_applied
        ]
        inventories = (
            list(
                session.exec(
                    select(Inventory)
                    .where(Inventory.id.in_(inventory_ids))
                    .with_for_update()
                ).all()
            )
            if inventory_ids
            else []
        )
        inventory_map = {inv.id: inv for inv in inventories}

        for line in sale.lines:
            if not line.is_active or line.inventory_applied:
                continue

            inventory = inventory_map.get(line.inventory_id)
            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory record not found for sale line",
                )
            if not inventory.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inactive inventory cannot be used in sales",
                )

            quantity = self._sale_line_quantity_boxes(line)
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
                source_type=InventorySourceType.SALE,
                event_type=InventoryEventType.SALE_APPROVED,
                movement_type=InventoryMovementType.OUT,
                value_type=InventoryValueType.PRICE,
                quantity=quantity,
                unit_value=line.price,
                prev_stock=prev_stock,
                new_stock=new_stock,
                inventory_id=inventory.id,
                sale_line_id=line.id,
            )

            inventory_repository.update(inventory, commit=False)
            movement_repository.add(movement, commit=False)
            line.inventory_applied = True
            session.add(line)

            movement_sequence += 1

    def _apply_sale_unpaid(self, sale: Sale) -> None:
        session = self.repository.db
        inventory_repository = InventoryRepository(session)
        movement_repository = InventoryMovementRepository(session)

        movement_group_id = str(sale.id)
        movement_sequence = movement_repository.get_next_sequence(movement_group_id)

        inventory_ids = [
            line.inventory_id
            for line in sale.lines
            if line.is_active and line.inventory_applied
        ]
        inventories = (
            list(
                session.exec(
                    select(Inventory)
                    .where(Inventory.id.in_(inventory_ids))
                    .with_for_update()
                ).all()
            )
            if inventory_ids
            else []
        )
        inventory_map = {inv.id: inv for inv in inventories}

        for line in sale.lines:
            if not line.is_active or not line.inventory_applied:
                continue

            inventory = inventory_map.get(line.inventory_id)
            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory record not found for sale line",
                )

            quantity = self._sale_line_quantity_boxes(line)
            prev_stock = inventory.stock
            new_stock = prev_stock + quantity

            inventory.stock = new_stock
            movement = InventoryMovement(
                movement_group_id=movement_group_id,
                movement_sequence=movement_sequence,
                source_type=InventorySourceType.SALE,
                event_type=InventoryEventType.SALE_REVERSED,
                movement_type=InventoryMovementType.IN_,
                value_type=InventoryValueType.PRICE,
                quantity=quantity,
                unit_value=line.price,
                prev_stock=prev_stock,
                new_stock=new_stock,
                inventory_id=inventory.id,
                sale_line_id=line.id,
            )

            inventory_repository.update(inventory, commit=False)
            movement_repository.add(movement, commit=False)
            line.inventory_applied = False
            session.add(line)

            movement_sequence += 1

    def list_sales(self, skip: int = 0, limit: int | None = None):
        return self.repository.list(skip=skip, limit=limit)

    def get_sale(self, sale_id: int):
        return self._get_sale_or_404(sale_id)

    def create_sale(self, payload: SaleCreateWithLines) -> Sale:
        if payload.status != SaleStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sale must be created in DRAFT status.",
            )

        sale = Sale(
            sale_date=payload.sale_date,
            status=payload.status,
            notes=payload.notes,
            client_id=payload.client_id,
        )

        for l in payload.lines:
            inventory = self._get_inventory_or_404(l.inventory_id)
            self._ensure_stock_available(inventory, l.quantity_boxes)
            line_values = self._line_snapshot_values(
                inventory,
                quantity_boxes=l.quantity_boxes,
                price=l.price,
                price_type=l.price_type,
            )
            sale.lines.append(
                SaleLine(
                    inventory_id=l.inventory_id,
                    quantity_units=line_values["quantity_units"],
                    box_size=line_values["box_size"],
                    price=line_values["price"],
                    price_type=line_values["price_type"],
                    unit_price=line_values["unit_price"],
                    box_price=line_values["box_price"],
                    total_price=line_values["total_price"],
                    product_code=line_values["product_code"],
                    product_name=line_values["product_name"],
                )
            )

        self._recalculate_sale_total(sale)

        try:
            self.repository.add(sale)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid client_id or inventory reference",
            )

        return self.repository.get(sale.id, include_inactive=True)  # type: ignore[return-value]

    def update_sale(self, sale_id: int, payload: SaleUpdate) -> Sale:
        sale = self._get_sale_or_404(sale_id)

        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(sale, field, value)

        try:
            self.repository.update(sale)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid client_id reference",
            )

        return self._get_sale_or_404(sale_id)

    def update_sale_status(
        self, sale_id: int, payload: SaleUpdateStatus, current_user=None
    ) -> Sale:
        session = self.repository.db

        try:
            # Avoid `InvalidRequestError: A transaction is already begun on this Session.`
            # A Session auto-begins a transaction on first DB interaction, so
            # using `with session.begin()` breaks if the caller already ran a
            # SELECT in the same session (e.g., seed scripts).
            #
            # This method is transactional and commits/rolls back explicitly to
            # ensure row locks are released deterministically.

            # Lock only the `sale` row. Querying the ORM entity here can include
            # eager outer joins (e.g., to `client`), and Postgres rejects
            # `FOR UPDATE` on the nullable side of an outer join.
            locked = (
                session.exec(
                    select(Sale.id)
                    .where(Sale.id == sale_id, Sale.is_active == True)  # noqa: E712
                    .with_for_update()
                ).first()
            )
            if not locked:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found"
                )

            sale = self._get_sale_or_404(sale_id)
            previous_status = sale.status
            new_status = payload.status

            if previous_status == new_status:
                session.commit()
                return sale

            allowed_transitions = {
                SaleStatus.DRAFT: {SaleStatus.PAID, SaleStatus.CANCELLED},
                SaleStatus.PAID: {SaleStatus.DRAFT, SaleStatus.CANCELLED},
                SaleStatus.CANCELLED: {SaleStatus.DRAFT},
            }
            if new_status not in allowed_transitions.get(previous_status, set()):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Invalid status transition.",
                )

            if new_status == SaleStatus.PAID:
                if current_user is not None:
                    sale.updated_by = getattr(current_user, "id", None)
                self._apply_sale_paid(sale)
            elif previous_status == SaleStatus.PAID:
                self._apply_sale_unpaid(sale)

            sale.status = new_status
            session.add(sale)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            state = _sqlstate(e)
            if state in {"22P02", "23514"} and "PAID" in str(getattr(e, "orig", e)):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Database schema does not accept sale.status='PAID'. "
                        "Run the one-time migration: `python -m src.shared.seed.cli "
                        "migrate-sales-approved-to-paid --yes`."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Integrity constraint violated while updating sale status.",
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
                        "Database schema does not accept sale.status='PAID'. "
                        "Run the one-time migration: `python -m src.shared.seed.cli "
                        "migrate-sales-approved-to-paid --yes`."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while updating sale status. Check server logs.",
            )
        except Exception:
            session.rollback()
            raise

        return self._get_sale_or_404(sale_id)

    def delete_sale(self, sale_id: int) -> Sale:
        sale = self._get_sale_or_404(sale_id)
        if sale.status == SaleStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete a PAID sale. Revert status first.",
            )
        self.repository.soft_delete(sale)
        return self.repository.get(sale_id, include_inactive=True)  # type: ignore[return-value]

    def add_sale_line(self, sale_id: int, payload: SaleLineCreate) -> SaleLine:
        session = self.repository.db
        sale = self._get_sale_or_404(sale_id)
        created_line: SaleLine | None = None

        try:
            def mutate() -> SaleLine:
                nonlocal created_line
                for existing in sale.lines:
                    if existing.is_active and existing.inventory_id == payload.inventory_id:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Duplicate inventory_id in sale lines is not allowed",
                        )

                inventory = self._get_inventory_or_404(payload.inventory_id)
                self._ensure_stock_available(inventory, payload.quantity_boxes)
                line_values = self._line_snapshot_values(
                    inventory,
                    quantity_boxes=payload.quantity_boxes,
                    price=payload.price,
                    price_type=payload.price_type,
                )
                line = SaleLine(
                    inventory_id=payload.inventory_id,
                    quantity_units=line_values["quantity_units"],
                    box_size=line_values["box_size"],
                    price=line_values["price"],
                    price_type=line_values["price_type"],
                    unit_price=line_values["unit_price"],
                    box_price=line_values["box_price"],
                    total_price=line_values["total_price"],
                    product_code=line_values["product_code"],
                    product_name=line_values["product_name"],
                )
                created_line = self.repository.add_line(sale, line, commit=False)
                return created_line

            self._apply_paid_sale_delta(sale, mutate)
            self.repository.update(sale, commit=False)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid inventory reference",
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
                detail="Failed to create sale line",
            )
        return created_line

    def update_sale_line(
        self, sale_id: int, line_id: int, payload: SaleLineUpdate
    ) -> SaleLine:
        session = self.repository.db
        line = self._get_line_or_404(sale_id, line_id)
        sale = line.sale or self._get_sale_or_404(sale_id)

        try:
            data = payload.model_dump(exclude_unset=True)

            def mutate() -> None:
                if "inventory_id" in data and sale:
                    for existing in sale.lines:
                        if (
                            existing.is_active
                            and existing.id != line.id
                            and existing.inventory_id == data["inventory_id"]
                        ):
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail="Duplicate inventory_id in sale lines is not allowed",
                            )

                next_inventory_id = data.get("inventory_id", line.inventory_id)
                inventory = self._get_inventory_or_404(next_inventory_id)

                next_quantity_boxes = data.get(
                    "quantity_boxes",
                    self._sale_line_quantity_boxes(line),
                )
                next_price_type = data.get("price_type", line.price_type)
                next_price = data.get("price", line.price)
                self._ensure_stock_available(inventory, int(next_quantity_boxes))
                line_values = self._line_snapshot_values(
                    inventory,
                    quantity_boxes=int(next_quantity_boxes),
                    price=next_price,
                    price_type=next_price_type,
                )

                for field, value in data.items():
                    if field == "quantity_boxes":
                        setattr(line, "quantity_units", int(value))
                    else:
                        setattr(line, field, value)

                line.inventory_id = inventory.id
                line.quantity_units = int(line_values["quantity_units"])
                line.box_size = int(line_values["box_size"])
                line.price = line_values["price"]
                line.price_type = line_values["price_type"]
                line.unit_price = line_values["unit_price"]
                line.box_price = line_values["box_price"]
                line.total_price = line_values["total_price"]
                line.product_code = line_values["product_code"]
                line.product_name = line_values["product_name"]

                self.repository.update_line(line, commit=False)

            self._apply_paid_sale_delta(sale, mutate)
            self.repository.update(sale, commit=False)
            session.commit()
        except HTTPException:
            session.rollback()
            raise
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid inventory reference",
            )
        except Exception:
            session.rollback()
            raise

        return line

    def delete_sale_line(self, sale_id: int, line_id: int) -> SaleLine:
        session = self.repository.db
        line = self._get_line_or_404(sale_id, line_id)
        sale = line.sale or self._get_sale_or_404(sale_id)

        try:
            def mutate() -> None:
                self.repository.soft_delete_line(line, commit=False)

            self._apply_paid_sale_delta(sale, mutate)
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
                    updated_by=sale.updated_by,
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
        """Genera el PDF de la factura para una venta específica (retorna bytes)"""
        sale = self._get_sale_or_404(sale_id)
        delivered_by_name = self._get_user_display_name(getattr(sale, "updated_by", None))
        pdf_bytes = self._pdf_generator.generate_sale_invoice_pdf(
            sale,
            delivered_by_name=delivered_by_name,
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="factura_{sale_id}.pdf"'},
        )
