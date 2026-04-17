from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, Response, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)
from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryCreateWithProduct,
    InventoryMovementFilters,
    InventoryUpdate,
)
from src.modules.product.domain.product_repository import ProductRepository
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)
from src.shared.files.image_validator import ImageValidator
from src.shared.files.upload_file_s3 import S3FileHandler
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.inventory_movement.inventory_movement_model import (
    InventoryMovement,
)
from src.shared.models.product.product_model import Product
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
        self._s3: S3FileHandler | None = None

    def _get_s3(self) -> S3FileHandler:
        if self._s3 is None:
            self._s3 = S3FileHandler()
        return self._s3

    def _get_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = self.repository.get(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory record not found",
            )
        return inventory

    def _get_product_or_404(self, product_id: int) -> Product:
        product = ProductRepository(self.repository.db).get(product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
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
                detail="Warehouse not found",
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
                detail="Invalid category_id reference",
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
                detail="Invalid brand_id reference",
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
                "Inventory already exists for this product, warehouse, and box size",
                [
                    {
                        "field": "product_id",
                        "message": "Duplicate inventory for selected warehouse and box size",
                    },
                    {
                        "field": "box_size",
                        "message": "This box size already exists for the selected product and warehouse",
                    },
                ],
            )

    def _upload_one_product_image(
        self, product_id: int, image: UploadFile
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
        return self._get_s3().upload_uploadfile(
            image,
            prefix=f"PRODUCT_IMAGES/{product_id}",
            make_public=True,
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
    ) -> InventoryMovement:
        return InventoryMovement(
            movement_group_id=str(uuid4()),
            movement_sequence=1,
            source_type=InventorySourceType.MANUAL,
            event_type=event_type,
            movement_type=movement_type,
            value_type=InventoryValueType.COST,
            quantity=quantity,
            unit_cost=inventory.last_cost,
            prev_stock=prev_stock,
            new_stock=new_stock,
            inventory_id=inventory.id,
        )

    def _record_manual_create(
        self, inventory: Inventory, movement_repository: InventoryMovementRepository
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
            ),
            commit=False,
        )

    def _ensure_unitary_placeholder(
        self,
        *,
        warehouse_id: int,
        product_id: int,
    ) -> None:
        existing_unitary_inventory = self.repository.get_by_keys(
            warehouse_id=warehouse_id,
            product_id=product_id,
            box_size=1,
        )
        if existing_unitary_inventory is not None:
            if not existing_unitary_inventory.is_active:
                existing_unitary_inventory.is_active = True
                self.repository.update(existing_unitary_inventory, commit=True)
            return

        unitary_inventory = Inventory(
            stock=0,
            box_size=1,
            avg_cost=Decimal("0.00"),
            last_cost=Decimal("0.00"),
            warehouse_id=warehouse_id,
            product_id=product_id,
            is_active=True,
        )

        try:
            self.repository.add(unitary_inventory, commit=True)
        except IntegrityError:
            self.repository.db.rollback()
            return

    def _expanded_inventory(self, inventory_id: int) -> Inventory:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory record not found",
            )
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
        return self._get_inventory_or_404(inventory_id)

    def create_inventory(self, payload: InventoryCreate) -> Inventory:
        self._get_product_or_404(payload.product_id)
        self._get_warehouse_or_404(payload.warehouse_id)
        self._ensure_inventory_unique(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            box_size=payload.box_size,
        )

        session = self.repository.db
        movement_repository = InventoryMovementRepository(session)
        inventory = Inventory(
            stock=payload.stock,
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
            self._record_manual_create(inventory, movement_repository)
            session.commit()
            if payload.box_size > 1:
                self._ensure_unitary_placeholder(
                    warehouse_id=payload.warehouse_id,
                    product_id=payload.product_id,
                )
        except IntegrityError:
            session.rollback()
            self._raise_conflict(
                "Inventory already exists for this product, warehouse, and box size",
                [
                    {
                        "field": "product_id",
                        "message": "Duplicate inventory for selected warehouse and box size",
                    }
                ],
            )

        return self._expanded_inventory(inventory.id)

    def create_inventory_with_product(
        self,
        payload: InventoryCreateWithProduct,
        image: UploadFile | None = None,
    ) -> Inventory:
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
                "Product data conflicts with an existing record",
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
                uploaded_key, image_url = self._upload_one_product_image(product.id, image)
                product.image = image_url
                product_repository.update(product, commit=False)

            self._ensure_inventory_unique(
                warehouse_id=payload.warehouse_id,
                product_id=product.id,
                box_size=payload.box_size,
            )

            inventory = Inventory(
                stock=payload.stock,
                box_size=payload.box_size,
                avg_cost=Decimal("0.00"),
                last_cost=Decimal("0.00"),
                warehouse_id=payload.warehouse_id,
                product_id=product.id,
                is_active=payload.is_active,
            )
            self.repository.add(inventory, commit=False)
            session.flush()
            self._record_manual_create(inventory, movement_repository)
            session.commit()
            if payload.box_size > 1:
                self._ensure_unitary_placeholder(
                    warehouse_id=payload.warehouse_id,
                    product_id=product.id,
                )
        except HTTPException:
            session.rollback()
            if uploaded_key:
                self._get_s3().delete_file(uploaded_key)
            raise
        except IntegrityError as exc:
            session.rollback()
            if uploaded_key:
                self._get_s3().delete_file(uploaded_key)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Integrity constraint violated while creating product inventory",
            ) from exc
        except Exception:
            session.rollback()
            if uploaded_key:
                self._get_s3().delete_file(uploaded_key)
            raise

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Inventory could not be created",
            )

        return self._expanded_inventory(inventory.id)

    def update_inventory(self, inventory_id: int, payload: InventoryUpdate) -> Inventory:
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
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            self._raise_conflict(
                "Inventory already exists for this product, warehouse, and box size",
                [
                    {
                        "field": "box_size",
                        "message": "This box size already exists for the selected product and warehouse",
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
    def list_movements(
        self, filters: InventoryMovementFilters, skip: int = 0, limit: Optional[int] = None
    ):
        movement_repository = InventoryMovementRepository(self.repository.db)
        return movement_repository.list(
            skip=skip,
            limit=limit,
            include_inactive=filters.include_inactive,
            inventory_id=filters.inventory_id,
            product_id=filters.product_id,
            warehouse_id=filters.warehouse_id,
            invoice_id=filters.invoice_id,
            invoice_line_id=filters.invoice_line_id,
            sale_id=filters.sale_id,
            sale_line_id=filters.sale_line_id,
            source_type=filters.source_type,
            event_type=filters.event_type,
            movement_type=filters.movement_type,
            value_type=filters.value_type,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )
