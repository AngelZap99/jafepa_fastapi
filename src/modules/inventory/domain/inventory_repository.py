from sqlalchemy.orm import Session, selectinload

from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.product.product_model import Product
from src.shared.models.warehouse.warehouse_model import Warehouse


class InventoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self, skip=0, limit=100):
        return (
            self.db.query(Inventory)
            .options(
                selectinload(Inventory.product).selectinload(Product.category),
                selectinload(Inventory.product).selectinload(Product.subcategory),
                selectinload(Inventory.product).selectinload(Product.brand),
                selectinload(Inventory.warehouse),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self):
        return (
            self.db.query(Inventory)
            .options(
                selectinload(Inventory.product),
                selectinload(Inventory.warehouse),
            )
            .all()
        )

    def get(self, inventory_id: int) -> Inventory | None:
        return (
            self.db.query(Inventory)
            .options(
                selectinload(Inventory.product),
                selectinload(Inventory.warehouse),
            )
            .filter(Inventory.id == inventory_id)
            .first()
        )

    def add(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    def update(self, inventory: Inventory) -> Inventory:
        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    def delete(self, inventory: Inventory):
        self.db.delete(inventory)
        self.db.commit()
