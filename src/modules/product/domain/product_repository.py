from sqlalchemy.orm import Session, selectinload
from src.shared.models.product.product_model import Product

class ProductRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self, skip=0, limit=100):
        return (
            self.db.query(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.subcategory),
                selectinload(Product.brand)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, product_id: int) -> Product | None:
        return (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

    def get_by_code(self, code: str) -> Product | None:
        return (
            self.db.query(Product)
            .filter(Product.code == code)
            .first()
        )

    def add(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product):
        self.db.delete(product)
        self.db.commit()
