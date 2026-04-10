from typing import List

from sqlalchemy.orm import Session, aliased, joinedload, selectinload
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.category.category_model import Category
from src.shared.models.product.product_model import Product
from src.shared.models.brand.brand_model import Brand
from src.shared.models.warehouse.warehouse_model import Warehouse


class InventoryRepository:

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _parse_int_filter(value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                return int(stripped)
        return None

    def _apply_inventory_filters(self, query, filters: dict | None):
        product_joined = False

        def ensure_product_join():
            nonlocal query, product_joined
            if not product_joined:
                query = query.join(Inventory.product)
                product_joined = True

        if not filters:
            return query

        ids = filters.get("ids")
        if ids:
            query = query.filter(Inventory.id.in_(ids))

        exclude_ids = filters.get("exclude_ids")
        if exclude_ids:
            query = query.filter(~Inventory.id.in_(exclude_ids))

        almacen = filters.get("almacen")
        if almacen is not None and almacen != "":
            warehouse_id = self._parse_int_filter(almacen)
            if warehouse_id is not None:
                query = query.filter(Inventory.warehouse_id == warehouse_id)
            else:
                query = query.filter(
                    Inventory.warehouse.has(Warehouse.name.ilike(almacen.strip()))
                )

        categoria = filters.get("categoria")
        if categoria is not None and categoria != "":
            ensure_product_join()
            category_id = self._parse_int_filter(categoria)
            if category_id is not None:
                query = query.filter(Product.category_id == category_id)
            else:
                category_alias = aliased(Category)
                query = query.join(category_alias, Product.category).filter(
                    category_alias.name.ilike(categoria.strip())
                )

        subcategoria = filters.get("subcategoria")
        if subcategoria is not None and subcategoria != "":
            ensure_product_join()
            subcategory_id = self._parse_int_filter(subcategoria)
            if subcategory_id is not None:
                query = query.filter(Product.subcategory_id == subcategory_id)
            else:
                subcategory_alias = aliased(Category)
                query = query.join(subcategory_alias, Product.subcategory).filter(
                    subcategory_alias.name.ilike(subcategoria.strip())
                )

        marca = filters.get("marca")
        if marca is not None and marca != "":
            ensure_product_join()
            brand_id = self._parse_int_filter(marca)
            if brand_id is not None:
                query = query.filter(Product.brand_id == brand_id)
            else:
                brand_alias = aliased(Brand)
                query = query.join(brand_alias, Product.brand).filter(
                    brand_alias.name.ilike(marca.strip())
                )

        buscar = filters.get("buscar")
        if buscar is not None and buscar.strip():
            ensure_product_join()
            search = f"%{buscar.strip()}%"
            query = query.filter(
                (Product.name.ilike(search)) | (Product.code.ilike(search))
            )

        return query

    def list(self, skip: int = 0, limit: int | None = None, filters: dict | None = None):
        q = (
            self.db.query(Inventory)
            .options(
                selectinload(Inventory.product).selectinload(Product.category),
                selectinload(Inventory.product).selectinload(Product.subcategory),
                selectinload(Inventory.product).selectinload(Product.brand),
                selectinload(Inventory.warehouse),
            )
        )
        q = self._apply_inventory_filters(q, filters).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return q.all()


    def list_all(self, filters: dict = None):
        query = self.db.query(Inventory).options(
            joinedload(Inventory.product).joinedload(Product.category),
            joinedload(Inventory.product).joinedload(Product.subcategory),
            joinedload(Inventory.product).joinedload(Product.brand),
            joinedload(Inventory.warehouse),
        )
        return self._apply_inventory_filters(query, filters).all()

    def get_report_warehouse(
        self,
        filters: dict | None = None,
        items: List[Inventory] | None = None,
    ) -> Warehouse | None:
        if items:
            for item in items:
                if item.warehouse and item.warehouse.is_active:
                    return item.warehouse

        query = self.db.query(Warehouse).filter(Warehouse.is_active == True)  # noqa: E712

        almacen = filters.get("almacen") if filters else None
        if almacen is not None and almacen != "":
            warehouse_id = self._parse_int_filter(almacen)
            if warehouse_id is not None:
                return query.filter(Warehouse.id == warehouse_id).order_by(Warehouse.id).first()
            return (
                query.filter(Warehouse.name.ilike(almacen.strip()))
                .order_by(Warehouse.id)
                .first()
            )

        return query.order_by(Warehouse.id).first()


    def get(self, inventory_id: int) -> Inventory | None:
        return (
            self.db.query(Inventory)
            .options(
                selectinload(Inventory.product).selectinload(Product.category),
                selectinload(Inventory.product).selectinload(Product.subcategory),
                selectinload(Inventory.product).selectinload(Product.brand),
                selectinload(Inventory.warehouse),
            )
            .filter(Inventory.id == inventory_id)
            .first()
        )

    def get_by_keys(
        self, warehouse_id: int, product_id: int, box_size: int
    ) -> Inventory | None:
        return (
            self.db.query(Inventory)
            .filter(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id,
                Inventory.box_size == box_size,
            )
            .first()
        )

    def warehouse_exists(self, warehouse_id: int) -> bool:
        return (
            self.db.query(Warehouse.id)
            .filter(Warehouse.id == warehouse_id, Warehouse.is_active == True)  # noqa: E712
            .first()
            is not None
        )

    def add(self, inventory: Inventory, commit: bool = True) -> Inventory:
        self.db.add(inventory)
        if commit:
            self.db.commit()
            self.db.refresh(inventory)
        return inventory

    def update(self, inventory: Inventory, commit: bool = True) -> Inventory:
        if commit:
            self.db.commit()
            self.db.refresh(inventory)
        return inventory

    def delete(self, inventory: Inventory):
        self.db.delete(inventory)
        self.db.commit()
