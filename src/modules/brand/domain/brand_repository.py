from sqlalchemy.orm import Session
from src.shared.models.brand.brand_model import Brand


class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int = 100):
        return self.db.query(Brand).offset(skip).limit(limit).all()

    def get(self, brand_id: int) -> Brand | None:
        return self.db.query(Brand).filter(Brand.id == brand_id).first()

    def get_by_name(self, name: str) -> Brand | None:
        return self.db.query(Brand).filter(Brand.name == name).first()

    def add(self, brand: Brand) -> Brand:
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def update(self, brand: Brand) -> Brand:
        self.db.commit()
        self.db.refresh(brand)
        return brand
