# src/modules/warehouse/domain/warehouse_repository.py

from sqlalchemy.orm import Session
from src.shared.models.warehouse.warehouse_model import Warehouse


class WarehouseRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self, skip=0, limit=100):
        return (
            self.db.query(Warehouse)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, warehouse_id: int) -> Warehouse | None:
        return (
            self.db.query(Warehouse)
            .filter(Warehouse.id == warehouse_id)
            .first()
        )

    def get_by_name(self, name: str) -> Warehouse | None:
        return (
            self.db.query(Warehouse)
            .filter(Warehouse.name == name)
            .first()
        )

    def add(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse

    def update(self, warehouse: Warehouse) -> Warehouse:
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse
