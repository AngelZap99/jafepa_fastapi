# src/modules/warehouse/domain/warehouse_repository.py
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.shared.models.warehouse.warehouse_model import Warehouse


class WarehouseRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int | None = None):
        q = select(Warehouse).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return self.db.execute(q).scalars().all()

    def get(self, warehouse_id: int) -> Warehouse | None:
        return self.db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        ).scalars().first()

    def get_by_name(self, name: str) -> Warehouse | None:
        return self.db.execute(
            select(Warehouse).where(Warehouse.name == name)
        ).scalars().first()

    def add(self, warehouse: Warehouse) -> Warehouse:
        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse

    def update(self, warehouse: Warehouse) -> Warehouse:
        self.db.commit()
        self.db.refresh(warehouse)
        return warehouse
