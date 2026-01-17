from typing import List
from fastapi import HTTPException, status

from src.shared.models.inventory.inventory_model import Inventory
from src.modules.inventory.inventory_schema import (
    InventoryCreate,
    InventoryUpdate,
    InventoryMovementFilters,
)

from src.modules.inventory.domain.inventory_repository import InventoryRepository
from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)

from fastapi.responses import FileResponse
from .pdf_generator import PDFGenerator


class InventoryService:

    ####################
    # Private methods
    ####################
    def __init__(self, repository: InventoryRepository) -> None:
        self.repository = repository
        self._pdf_generator = PDFGenerator()

    def _get_inventory_or_404(self, inventory_id: int) -> Inventory:
        inventory = self.repository.get(inventory_id)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory record not found",
            )
        return inventory

    ####################
    # Public methods
    ####################
    def list_inventory(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        return self.repository.list(skip=skip, limit=limit)

    def get_inventory(self, inventory_id: int) -> Inventory:
        return self._get_inventory_or_404(inventory_id)

    def create_inventory(self, payload: InventoryCreate) -> Inventory:
        inventory = Inventory(
            stock=payload.stock,
            box_size=payload.box_size,
            avg_cost=payload.avg_cost,
            last_cost=payload.last_cost,
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            is_active=True,
        )

        return self.repository.add(inventory)

    def update_inventory(self, inventory_id: int, payload: InventoryUpdate) -> Inventory:
        inventory = self._get_inventory_or_404(inventory_id)
        data = payload.model_dump(exclude_unset=True)

        # Aplicar cambios al modelo
        for field, value in data.items():
            setattr(inventory, field, value)

        return self.repository.update(inventory)

    def delete_inventory(self, inventory_id: int) -> Inventory:
        inventory = self._get_inventory_or_404(inventory_id)
        inventory.is_active = False
        self.repository.update(inventory)
        return inventory

    ####################
    # PDF methods
    ####################
    def generate_all_inventory_pdf(self, filters: dict = None):
        # Llamamos a list_all y le pasamos filtros si vienen
        items = self.repository.list_all(filters=filters)
        
        # Generar PDF con tu generador
        pdf_path = self._pdf_generator.generate_inventory_pdf(items)

        return FileResponse(pdf_path, filename="inventory.pdf")

    ####################
    # Movement history
    ####################
    def list_movements(
        self, filters: InventoryMovementFilters, skip: int = 0, limit: int = 100
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
            source_type=filters.source_type,
            event_type=filters.event_type,
            movement_type=filters.movement_type,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )
