from sqlalchemy.orm import Session, selectinload
from src.shared.models.product.product_model import Product
from typing import List, Dict

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip=0, limit=100):
        return (
            self.db.query(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.subcategory),
                selectinload(Product.brand),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, product_id: int) -> Product | None:
        return (
            self.db.query(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.subcategory),
                selectinload(Product.brand),
            )
            .filter(Product.id == product_id)
            .first()
        )

    def get_by_code(self, code: str) -> Product | None:
        code = str(code).strip().upper()
        return self.db.query(Product).filter(Product.code == code).first()

    def get_by_name(self, name: str) -> Product | None:
        return self.db.query(Product).filter(Product.name == name).first()

    def add(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product):
        self.db.delete(product)
        self.db.commit()

    # ✅ Cambio aquí: list[dict] -> List[Dict]
    def check_conflicts(self, payload, product_id: int | None = None) -> List[Dict]:
        conflicts = []

        # Código duplicado
        existing_code = self.get_by_code(payload.code)
        if existing_code and (product_id is None or existing_code.id != product_id):
            conflicts.append({"field": "code", "message": f"El código '{payload.code}' ya está registrado"})

        # Nombre duplicado
        existing_name = self.get_by_name(payload.name)
        if existing_name and (product_id is None or existing_name.id != product_id):
            conflicts.append({"field": "name", "message": f"El nombre '{payload.name}' ya existe"})

        return conflicts
