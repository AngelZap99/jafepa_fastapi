# src/modules/warehouse/domain/warehouse_service.py

from typing import List
from fastapi import HTTPException, status

from src.shared.models.warehouse.warehouse_model import Warehouse
from src.modules.warehouse.warehouse_schema import (
    WarehouseCreate,
    WarehouseUpdate,
)
from src.modules.warehouse.domain.warehouse_repository import WarehouseRepository


class WarehouseService:
    ####################
    # Private methods
    ####################
    def __init__(self, repository: WarehouseRepository) -> None:
        self.repository = repository

    def _ensure_name_not_taken(
        self, name: str, warehouse_owner_id: int | None = None
    ) -> None:
        existing = self.repository.get_by_name(name)

        if existing and (warehouse_owner_id is None or existing.id != warehouse_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El nombre del almacén '{name}' ya está en uso",
            )

    def _get_warehouse_or_404(self, warehouse_id: int) -> Warehouse:
        warehouse = self.repository.get(warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Almacén no encontrado",
            )
        return warehouse

    ####################
    # Public methods
    ####################
    def list_warehouses(self, skip: int = 0, limit: int | None = None) -> List[Warehouse]:
        return self.repository.list(skip=skip, limit=limit)

    def get_warehouse(self, warehouse_id: int) -> Warehouse:
        return self._get_warehouse_or_404(warehouse_id)

    def create_warehouse(self, payload: WarehouseCreate) -> Warehouse:
        self._ensure_name_not_taken(payload.name)

        warehouse = Warehouse(
            name=payload.name,
            address=payload.address,
            email=payload.email,
            phone=payload.phone,
            is_active=True,
        )

        return self.repository.add(warehouse)

    def update_warehouse(self, warehouse_id: int, payload: WarehouseUpdate) -> Warehouse:
        warehouse = self._get_warehouse_or_404(warehouse_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data:
            self._ensure_name_not_taken(data["name"], warehouse_owner_id=warehouse.id)

        # Aplicar cambios
        for field, value in data.items():
            setattr(warehouse, field, value)

        return self.repository.update(warehouse)

    def delete_warehouse(self, warehouse_id: int) -> Warehouse:
        warehouse = self._get_warehouse_or_404(warehouse_id)
        warehouse.is_active = False
        self.repository.update(warehouse)
        return warehouse
