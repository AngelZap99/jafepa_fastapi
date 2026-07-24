from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, Response, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.domain.inventory_history_xlsx import (
    build_inventory_history_xlsx,
    format_history_datetime,
)
from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryCreateWithProduct,
    InventoryMovementFilters,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    InventoryOperationalHistoryItem,
    InventoryOperationalHistoryResponse,
    InventoryOperationalHistorySummary,
    InventoryUpdate,
)
from src.modules.product.domain.product_repository import ProductRepository
from src.modules.users.domain.users_repository import UserRepository
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.files.image_validator import ImageValidator
from src.shared.enums.sale_enums import SaleLineQuantityMode
from src.shared.files.local_file_storage import LocalFileHandler
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.product.product_model import Product
from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.models.warehouse.warehouse_model import Warehouse

from .pdf_generator import PDFGenerator


class InventoryService:

    ####################
    # Private methods
    ####################
    def __init__(self, repository: InventoryRepository) -> None:
        self.repository = repository
        self._pdf_generator = PDFGenerator()
        self._image_validator = ImageValidator()
        self._storage: LocalFileHandler | None = None

    def _get_storage(self) -> LocalFileHandler:
        if self._storage is None:
            self._storage = LocalFileHandler()
        return self._storage

    def _get_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = self.repository.get(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de inventario no encontrado",
            )
        return inventory

    def _get_product_or_404(self, product_id: int) -> Product:
        product = ProductRepository(self.repository.db).get(product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )
        return product

    def _get_warehouse_or_404(self, warehouse_id: int) -> Warehouse:
        warehouse = (
            self.repository.db.exec(
                select(Warehouse).where(
                    Warehouse.id == warehouse_id, Warehouse.is_active == True  # noqa: E712
                )
            ).first()
        )
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Almacén no encontrado",
            )
        return warehouse

    def _ensure_category_refs_exist(
        self,
        *,
        category_id: int,
        brand_id: int,
    ) -> None:
        session = self.repository.db

        category_exists = (
            session.exec(
                select(Category.id).where(
                    Category.id == category_id, Category.is_active == True  # noqa: E712
                )
            ).first()
        )
        if category_exists is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La categoría seleccionada no es válida",
            )

        brand_exists = (
            session.exec(
                select(Brand.id).where(
                    Brand.id == brand_id, Brand.is_active == True  # noqa: E712
                )
            ).first()
        )
        if brand_exists is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La marca seleccionada no es válida",
            )

    def _raise_conflict(self, message: str, errors: list[dict]) -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": message, "errors": errors},
        )

    def _ensure_inventory_unique(
        self,
        *,
        warehouse_id: int,
        product_id: int,
        box_size: int,
        current_inventory_id: int | None = None,
    ) -> None:
        existing = self.repository.get_by_keys(
            warehouse_id=warehouse_id,
            product_id=product_id,
            box_size=box_size,
        )
        if existing and existing.id != current_inventory_id:
            self._raise_conflict(
                "Ya existe un inventario para este producto, almacén y tamaño de caja.",
                [
                    {
                        "field": "product_id",
                        "message": "Ya existe un inventario para el almacén y tamaño de caja seleccionados.",
                    },
                    {
                        "field": "box_size",
                        "message": "Este tamaño de caja ya existe para el producto y almacén seleccionados.",
                    },
                ],
            )

    def _upload_one_product_image(
        self, product_id: int, image: UploadFile, *, base_url: str | None = None
    ) -> tuple[str, str]:
        try:
            self._image_validator.validate(
                [image],
                max_size_bytes=5 * 1024 * 1024,
                allowed_extensions={".jpg", ".jpeg", ".png", ".webp"},
                allowed_mime_types={"image/jpeg", "image/png", "image/webp"},
                require_magic_bytes=True,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return self._get_storage().upload_uploadfile(
            image,
            prefix=f"product-images/{product_id}",
            make_public=True,
            base_url=base_url,
        )

    def _build_manual_movement(
        self,
        *,
        inventory: Inventory,
        event_type: InventoryEventType,
        movement_type: InventoryMovementType,
        quantity: int,
        prev_stock: int,
        new_stock: int,
        actor_id: int | None = None,
    ) -> InventoryMovement:
        return InventoryMovement(
            movement_group_id=str(uuid4()),
            movement_sequence=1,
            source_type=InventorySourceType.MANUAL,
            event_type=event_type,
            movement_type=movement_type,
            value_type=InventoryValueType.COST,
            quantity=quantity,
            unit_value=inventory.last_cost,
            prev_stock=prev_stock,
            new_stock=new_stock,
            inventory_id=inventory.id,
            created_by=actor_id,
            updated_by=actor_id,
        )

    def _record_manual_create(
        self,
        inventory: Inventory,
        movement_repository: InventoryMovementRepository,
        actor_id: int | None = None,
    ) -> None:
        if inventory.stock <= 0:
            return
        movement_repository.add(
            self._build_manual_movement(
                inventory=inventory,
                event_type=InventoryEventType.MANUAL_CREATED,
                movement_type=InventoryMovementType.IN_,
                quantity=inventory.stock,
                prev_stock=0,
                new_stock=inventory.stock,
                actor_id=actor_id,
            ),
            commit=False,
        )

    def _record_manual_stock_adjustment(
        self,
        *,
        inventory: Inventory,
        prev_stock: int,
        new_stock: int,
        movement_repository: InventoryMovementRepository,
        actor_id: int | None = None,
    ) -> None:
        delta = new_stock - prev_stock
        if delta == 0:
            return

        movement_repository.add(
            self._build_manual_movement(
                inventory=inventory,
                event_type=InventoryEventType.MANUAL_STOCK_ADJUSTED,
                movement_type=(
                    InventoryMovementType.IN_
                    if delta > 0
                    else InventoryMovementType.OUT
                ),
                quantity=abs(delta),
                prev_stock=prev_stock,
                new_stock=new_stock,
                actor_id=actor_id,
            ),
            commit=False,
        )

    def _ensure_unitary_placeholder(
        self,
        *,
        warehouse_id: int,
        product_id: int,
        commit: bool = True,
    ) -> None:
        existing_unitary_inventory = self.repository.get_by_keys(
            warehouse_id=warehouse_id,
            product_id=product_id,
            box_size=1,
        )
        if existing_unitary_inventory is not None:
            if not existing_unitary_inventory.is_active:
                existing_unitary_inventory.is_active = True
                self.repository.update(existing_unitary_inventory, commit=commit)
            return

        unitary_inventory = Inventory(
            stock=0,
            reserved_stock=0,
            box_size=1,
            avg_cost=Decimal("0.00"),
            last_cost=Decimal("0.00"),
            warehouse_id=warehouse_id,
            product_id=product_id,
            is_active=True,
        )

        try:
            self.repository.add(unitary_inventory, commit=commit)
        except IntegrityError:
            self.repository.db.rollback()
            return

    def _expanded_inventory(self, inventory_id: int) -> Inventory:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de inventario no encontrado",
            )
        return inventory

    def _attach_active_reservations(self, inventory: Inventory) -> Inventory:
        reservations = list(
            self.repository.db.exec(
                select(SaleLine)
                .join(SaleLine.sale)
                .join(SaleLine.inventory)
                .where(
                    SaleLine.is_active == True,  # noqa: E712
                    SaleLine.reservation_applied == True,  # noqa: E712
                    Sale.is_active == True,  # noqa: E712
                    Sale.status == "DRAFT",
                    Inventory.product_id == inventory.product_id,
                    Inventory.warehouse_id == inventory.warehouse_id,
                )
                .order_by(Sale.updated_at.desc(), Sale.id.desc(), SaleLine.id.desc())
            ).all()
        )

        payload = []
        for line in reservations:
            sale = line.sale
            source_inventory = line.inventory
            if not sale or not source_inventory:
                continue
            affects_source = line.inventory_id == inventory.id
            affects_unit_inventory = (
                inventory.box_size == 1
                and line.quantity_mode == SaleLineQuantityMode.UNIT
                and source_inventory.product_id == inventory.product_id
                and source_inventory.warehouse_id == inventory.warehouse_id
            )
            if not affects_source and not affects_unit_inventory:
                continue

            source_box_size = None
            projected_units_from_stock = None
            projected_boxes_to_open = None
            projected_units_leftover = None
            if line.quantity_mode == SaleLineQuantityMode.UNIT:
                current_line_reserved_units = int(line.quantity_units) if line.reservation_applied else 0
                if int(source_inventory.box_size or 1) > 1:
                    unit_inventory = self.repository.db.exec(
                        select(Inventory).where(
                            Inventory.warehouse_id == source_inventory.warehouse_id,
                            Inventory.product_id == source_inventory.product_id,
                            Inventory.box_size == 1,
                        )
                    ).first()
                    unit_stock = int(unit_inventory.stock) if unit_inventory else 0
                    unit_reserved = int(unit_inventory.reserved_stock) if unit_inventory else 0
                    available_units = max(
                        unit_stock - max(unit_reserved - current_line_reserved_units, 0),
                        0,
                    )
                    projected_units_from_stock = min(int(line.quantity_units), available_units)
                    remaining_units = max(
                        int(line.quantity_units) - projected_units_from_stock,
                        0,
                    )
                    source_box_size = int(source_inventory.box_size or 1)
                    projected_boxes_to_open = (
                        ceil(remaining_units / source_box_size)
                        if remaining_units > 0
                        else 0
                    )
                    projected_units_leftover = (
                        projected_boxes_to_open * source_box_size - remaining_units
                        if projected_boxes_to_open > 0
                        else 0
                    )
                else:
                    available_units = max(
                        int(source_inventory.stock)
                        - max(
                            int(source_inventory.reserved_stock) - current_line_reserved_units,
                            0,
                        ),
                        0,
                    )
                    projected_units_from_stock = min(int(line.quantity_units), available_units)
                    source_box_size = int(source_inventory.box_size or 1)
                    projected_boxes_to_open = 0
                    projected_units_leftover = 0
            payload.append(
                {
                    "sale_line_id": line.id,
                    "sale_id": sale.id,
                    "quantity_boxes": line.quantity_boxes,
                    "quantity_mode": line.quantity_mode,
                    "price": line.price,
                    "price_type": line.price_type,
                    "total_price": line.total_price,
                    "product_code": line.product_code,
                    "product_name": line.product_name,
                    "source_box_size": source_box_size,
                    "projected_units_from_stock": projected_units_from_stock,
                    "projected_boxes_to_open": projected_boxes_to_open,
                    "projected_units_leftover": projected_units_leftover,
                    "sale": sale,
                }
            )

        object.__setattr__(inventory, "active_reservations", payload)
        return inventory

    ####################
    # Public methods
    ####################
    def list_inventory(
        self,
        skip: int = 0,
        limit: Optional[int] = None,
        filters: dict | None = None,
    ) -> List[Inventory]:
        return self.repository.list(skip=skip, limit=limit, filters=filters)

    def get_inventory(self, inventory_id: int) -> Inventory:
        return self._attach_active_reservations(self._get_inventory_or_404(inventory_id))

    def create_inventory(self, payload: InventoryCreate, current_user=None) -> Inventory:
        actor_id = getattr(current_user, "id", None)
        self._get_product_or_404(payload.product_id)
        self._get_warehouse_or_404(payload.warehouse_id)

        existing_inventory = self.repository.get_by_keys(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            box_size=payload.box_size,
        )

        session = self.repository.db
        movement_repository = InventoryMovementRepository(session)

        if existing_inventory is not None:
            prev_stock = existing_inventory.stock
            existing_inventory.stock = prev_stock + payload.stock
            existing_inventory.is_active = True

            try:
                self.repository.update(existing_inventory, commit=False)
                self._record_manual_stock_adjustment(
                    inventory=existing_inventory,
                    prev_stock=prev_stock,
                    new_stock=existing_inventory.stock,
                    movement_repository=movement_repository,
                    actor_id=actor_id,
                )
                if payload.box_size > 1:
                    self._ensure_unitary_placeholder(
                        warehouse_id=payload.warehouse_id,
                        product_id=payload.product_id,
                        commit=False,
                    )
                session.commit()
            except IntegrityError:
                session.rollback()
                self._raise_conflict(
                    "Ya existe un inventario para este producto, almacén y tamaño de caja.",
                    [
                        {
                            "field": "product_id",
                            "message": "Ya existe un inventario para el almacén y tamaño de caja seleccionados.",
                        }
                    ],
                )
            except Exception:
                session.rollback()
                raise

            return self._expanded_inventory(existing_inventory.id)

        inventory = Inventory(
            stock=payload.stock,
            reserved_stock=0,
            box_size=payload.box_size,
            avg_cost=Decimal("0.00"),
            last_cost=Decimal("0.00"),
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            is_active=payload.is_active,
        )

        try:
            self.repository.add(inventory, commit=False)
            session.flush()
            self._record_manual_create(inventory, movement_repository, actor_id=actor_id)
            if payload.box_size > 1:
                self._ensure_unitary_placeholder(
                    warehouse_id=payload.warehouse_id,
                    product_id=payload.product_id,
                    commit=False,
                )
            session.commit()
        except IntegrityError:
            session.rollback()
            self._raise_conflict(
                "Ya existe un inventario para este producto, almacén y tamaño de caja.",
                [
                    {
                        "field": "product_id",
                        "message": "Ya existe un inventario para el almacén y tamaño de caja seleccionados.",
                    }
                ],
            )
        except Exception:
            session.rollback()
            raise

        return self._expanded_inventory(inventory.id)

    def create_inventory_with_product(
        self,
        payload: InventoryCreateWithProduct,
        image: UploadFile | None = None,
        *,
        base_url: str | None = None,
        current_user=None,
    ) -> Inventory:
        actor_id = getattr(current_user, "id", None)
        session = self.repository.db
        product_repository = ProductRepository(session)
        movement_repository = InventoryMovementRepository(session)

        self._get_warehouse_or_404(payload.warehouse_id)
        self._ensure_category_refs_exist(
            category_id=payload.category_id,
            brand_id=payload.brand_id,
        )

        product_conflicts = product_repository.check_conflicts(payload)
        if product_conflicts:
            self._raise_conflict(
                "Los datos del producto entran en conflicto con un registro existente.",
                product_conflicts,
            )

        product = Product(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            image=None,
            is_active=True,
        )

        uploaded_key: str | None = None
        inventory: Inventory | None = None

        try:
            product_repository.add(product, commit=False)
            session.flush()

            if image:
                uploaded_key, _image_url = self._upload_one_product_image(
                    product.id, image, base_url=base_url
                )
                product.image = uploaded_key
                product_repository.update(product, commit=False)

            self._ensure_inventory_unique(
                warehouse_id=payload.warehouse_id,
                product_id=product.id,
                box_size=payload.box_size,
            )

            inventory = Inventory(
                stock=payload.stock,
                reserved_stock=0,
                box_size=payload.box_size,
                avg_cost=Decimal("0.00"),
                last_cost=Decimal("0.00"),
                warehouse_id=payload.warehouse_id,
                product_id=product.id,
                is_active=payload.is_active,
            )
            self.repository.add(inventory, commit=False)
            session.flush()
            self._record_manual_create(inventory, movement_repository, actor_id=actor_id)
            if payload.box_size > 1:
                self._ensure_unitary_placeholder(
                    warehouse_id=payload.warehouse_id,
                    product_id=product.id,
                    commit=False,
                )
            session.commit()
        except HTTPException:
            session.rollback()
            if uploaded_key:
                self._get_storage().delete_file(uploaded_key)
            raise
        except IntegrityError as exc:
            session.rollback()
            if uploaded_key:
                self._get_storage().delete_file(uploaded_key)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo crear el inventario del producto.",
            ) from exc
        except Exception:
            session.rollback()
            if uploaded_key:
                self._get_storage().delete_file(uploaded_key)
            raise

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo crear el inventario.",
            )

        return self._expanded_inventory(inventory.id)

    def update_inventory(
        self, inventory_id: int, payload: InventoryUpdate, current_user=None
    ) -> Inventory:
        actor_id = getattr(current_user, "id", None)
        inventory = self._get_inventory_or_404(inventory_id)
        data = payload.model_dump(exclude_unset=True)
        prev_stock = inventory.stock
        new_box_size = data.get("box_size", inventory.box_size)

        if new_box_size != inventory.box_size:
            self._ensure_inventory_unique(
                warehouse_id=inventory.warehouse_id,
                product_id=inventory.product_id,
                box_size=new_box_size,
                current_inventory_id=inventory.id,
            )

        for field, value in data.items():
            setattr(inventory, field, value)

        session = self.repository.db
        movement_repository = InventoryMovementRepository(session)

        try:
            self.repository.update(inventory, commit=False)
            self._record_manual_stock_adjustment(
                inventory=inventory,
                prev_stock=prev_stock,
                new_stock=inventory.stock,
                movement_repository=movement_repository,
                actor_id=actor_id,
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            self._raise_conflict(
                "Ya existe un inventario para este producto, almacén y tamaño de caja.",
                [
                    {
                        "field": "box_size",
                        "message": "Este tamaño de caja ya existe para el producto y almacén seleccionados.",
                    }
                ],
            )

        return self._expanded_inventory(inventory.id)

    def delete_inventory(self, inventory_id: int) -> Inventory:
        inventory = self._get_inventory_or_404(inventory_id)
        inventory.is_active = False
        self.repository.update(inventory)
        return self._expanded_inventory(inventory.id)

    ####################
    # PDF methods
    ####################
    def generate_all_inventory_pdf(self, filters: dict = None):
        items = self.repository.list_all(filters=filters)
        report_warehouse = self.repository.get_report_warehouse(filters=filters, items=items)

        try:
            pdf_bytes = self._pdf_generator.generate_inventory_pdf(
                items,
                warehouse=report_warehouse,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="inventory.pdf"'},
        )

    ####################
    # Movement history
    ####################
    def _movement_actor(self, movement: InventoryMovement) -> tuple[int | None, str]:
        if movement.created_by:
            return movement.created_by, "movement"

        sale = movement.sale_line.sale if movement.sale_line else None
        if sale is not None:
            if movement.event_type == InventoryEventType.SALE_APPROVED:
                return (
                    sale.paid_by or sale.updated_by or sale.created_by,
                    "sale",
                )
            if movement.event_type in {
                InventoryEventType.SALE_REVERSED,
                InventoryEventType.SALE_RELEASED,
            }:
                return (
                    sale.cancelled_by or sale.updated_by or sale.created_by,
                    "sale",
                )
            if movement.event_type == InventoryEventType.SALE_RESERVED:
                return sale.updated_by or sale.created_by, "sale"
            return sale.updated_by or sale.created_by, "sale"

        invoice = movement.invoice_line.invoice if movement.invoice_line else None
        if invoice is not None:
            return invoice.updated_by or invoice.created_by, "invoice"

        return None, "unknown"

    def _user_display_name(self, user_id: int | None, cache: dict[int, str | None]) -> str | None:
        if not user_id:
            return None
        if user_id not in cache:
            user = UserRepository(self.repository.db).get(user_id)
            cache[user_id] = (
                f"{user.first_name} {user.last_name}".strip()
                if user
                else None
            )
        return cache[user_id]

    def _movement_response(
        self, movement: InventoryMovement, user_cache: dict[int, str | None]
    ) -> InventoryMovementResponse:
        actor_user_id, actor_source = self._movement_actor(movement)
        actor_name = self._user_display_name(actor_user_id, user_cache)
        payload = InventoryMovementResponse.model_validate(movement, from_attributes=True)
        payload.actor_user_id = actor_user_id
        payload.actor_name = actor_name
        payload.actor_source = actor_source if actor_user_id else "unknown"
        return payload

    def list_movements(
        self, filters: InventoryMovementFilters, skip: int = 0, limit: Optional[int] = None
    ) -> InventoryMovementListResponse:
        movement_repository = InventoryMovementRepository(self.repository.db)
        filter_kwargs = {
            "include_inactive": filters.include_inactive,
            "inventory_id": filters.inventory_id,
            "product_id": filters.product_id,
            "warehouse_id": filters.warehouse_id,
            "created_by": filters.created_by,
            "invoice_id": filters.invoice_id,
            "invoice_line_id": filters.invoice_line_id,
            "sale_id": filters.sale_id,
            "sale_line_id": filters.sale_line_id,
            "source_type": filters.source_type,
            "event_type": filters.event_type,
            "movement_type": filters.movement_type,
            "value_type": filters.value_type,
            "from_date": filters.from_date,
            "to_date": filters.to_date,
        }
        movements = movement_repository.list(
            skip=skip,
            limit=limit,
            **filter_kwargs,
        )
        total = movement_repository.count(**filter_kwargs)
        user_cache: dict[int, str | None] = {}
        return InventoryMovementListResponse(
            items=[
                self._movement_response(movement, user_cache)
                for movement in movements
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_operational_history(
        self,
        *,
        inventory_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        movement_type: InventoryMovementType | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> InventoryOperationalHistoryResponse:
        inventory = self._get_inventory_or_404(inventory_id)
        movement_repository = InventoryMovementRepository(self.repository.db)
        movements = movement_repository.list_operational(
            inventory_id=inventory_id,
            skip=skip,
            limit=limit,
            movement_type=movement_type,
            from_date=from_date,
            to_date=to_date,
        )
        total = movement_repository.count_operational(
            inventory_id=inventory_id,
            movement_type=movement_type,
            from_date=from_date,
            to_date=to_date,
        )
        entries, exits = movement_repository.operational_totals(
            inventory_id=inventory_id,
            movement_type=movement_type,
            from_date=from_date,
            to_date=to_date,
        )

        items: list[InventoryOperationalHistoryItem] = []
        user_cache: dict[int, str | None] = {}
        for movement in movements:
            operation_type = "ADJUSTMENT"
            client_name = None
            reference_id = None
            reference_number = None
            reference_sequence = None

            if movement.event_type == InventoryEventType.INVOICE_RECEIVED:
                operation_type = "PURCHASE"
                invoice = (
                    movement.invoice_line.invoice if movement.invoice_line else None
                )
                if invoice is not None:
                    reference_id = invoice.id
                    reference_number = invoice.invoice_number
                    reference_sequence = invoice.sequence
            elif movement.event_type == InventoryEventType.SALE_APPROVED:
                operation_type = "SALE"
                sale = movement.sale_line.sale if movement.sale_line else None
                if sale is not None:
                    reference_id = sale.id
                    client_name = sale.client.name if sale.client else None

            actor_user_id, _ = self._movement_actor(movement)
            items.append(
                InventoryOperationalHistoryItem(
                    id=movement.id,
                    movement_date=movement.movement_date,
                    operation_type=operation_type,
                    movement_type=movement.movement_type,
                    quantity=movement.quantity,
                    client_name=client_name,
                    actor_name=self._user_display_name(actor_user_id, user_cache),
                    unit_value=movement.unit_value,
                    total_value=movement.unit_value * Decimal(movement.quantity),
                    reference_id=reference_id,
                    reference_number=reference_number,
                    reference_sequence=reference_sequence,
                )
            )

        return InventoryOperationalHistoryResponse(
            inventory_id=inventory.id,
            box_size=inventory.box_size,
            summary=InventoryOperationalHistorySummary(
                entries=entries,
                available=inventory.stock - inventory.reserved_stock,
                physical_stock=inventory.stock,
                reserved_stock=inventory.reserved_stock,
                exits=exits,
            ),
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    def export_operational_history_xlsx(
        self,
        *,
        inventory_id: int,
        movement_type: InventoryMovementType | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> bytes:
        inventory = self._get_inventory_or_404(inventory_id)
        history = self.get_operational_history(
            inventory_id=inventory_id,
            skip=0,
            limit=None,
            movement_type=movement_type,
            from_date=from_date,
            to_date=to_date,
        )

        filter_parts: list[str] = []
        if from_date and to_date:
            filter_parts.append(
                f"{from_date.strftime('%d/%m/%Y')} al {to_date.strftime('%d/%m/%Y')}"
            )
        elif from_date:
            filter_parts.append(f"Desde {from_date.strftime('%d/%m/%Y')}")
        elif to_date:
            filter_parts.append(f"Hasta {to_date.strftime('%d/%m/%Y')}")
        if movement_type is not None:
            filter_parts.append(
                "Solo entradas"
                if movement_type == InventoryMovementType.IN_
                else "Solo salidas"
            )

        rows = []
        for item in history.items:
            if item.operation_type == "SALE":
                operation = (
                    f"Venta #{item.reference_id}" if item.reference_id else "Venta"
                )
            elif item.operation_type == "PURCHASE":
                if item.reference_number:
                    sequence = (
                        f"-{item.reference_sequence}"
                        if item.reference_sequence
                        else ""
                    )
                    operation = f"Factura {item.reference_number}{sequence}"
                else:
                    operation = (
                        f"Factura #{item.reference_id}"
                        if item.reference_id
                        else "Factura"
                    )
            else:
                operation = "Ajuste manual"

            rows.append(
                {
                    "quantity": item.quantity,
                    "operation": operation,
                    "movement_type": (
                        "Entrada"
                        if item.movement_type == InventoryMovementType.IN_
                        else "Salida"
                    ),
                    "client_name": item.client_name or "",
                    "actor_name": item.actor_name or "",
                    "unit_value": item.unit_value,
                    "total_value": item.total_value,
                    "movement_date": format_history_datetime(item.movement_date),
                }
            )

        product = inventory.product
        warehouse = inventory.warehouse
        product_title = " - ".join(
            value
            for value in [
                getattr(product, "code", None),
                getattr(product, "name", None),
            ]
            if value
        )
        presentation = (
            f"Caja de {inventory.box_size} piezas"
            if inventory.box_size > 1
            else "Pieza individual"
        )
        return build_inventory_history_xlsx(
            title=product_title,
            warehouse=getattr(warehouse, "name", "") or "",
            presentation=presentation,
            filter_description=" · ".join(filter_parts) or "Sin filtros",
            entries=history.summary.entries,
            exits=history.summary.exits,
            available=history.summary.available,
            rows=rows,
        )
