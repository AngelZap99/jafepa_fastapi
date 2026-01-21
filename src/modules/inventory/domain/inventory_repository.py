from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm import joinedload
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


    def list_all(self, filters: dict = None):
        query = self.db.query(Inventory).options(
            joinedload(Inventory.product),
            joinedload(Inventory.warehouse)
        )

        if filters:
            if "ids" in filters:
                query = query.filter(Inventory.id.in_(filters["ids"]))

            if "categoria" in filters:
                query = query.join(Inventory.product).filter(Product.category_id == filters["categoria"])

            if "subcategoria" in filters:
                query = query.join(Inventory.product).filter(Product.subcategory_id == filters["subcategoria"])

            if "marca" in filters:
                query = query.join(Inventory.product).filter(Product.brand_id == filters["marca"])

            if "buscar" in filters:
                search = f"%{filters['buscar']}%"
                query = query.join(Inventory.product).filter(
                    (Product.name.ilike(search)) |
                    (Product.code.ilike(search))
                )

        return query.all()


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
