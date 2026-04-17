from sqlalchemy import select
from sqlalchemy.orm import Session
from src.shared.models.brand.brand_model import Brand


class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int | None = None):
        q = select(Brand).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return self.db.execute(q).scalars().all()

    def get(self, brand_id: int) -> Brand | None:
        return self.db.execute(select(Brand).where(Brand.id == brand_id)).scalars().first()

    def get_by_name(self, name: str) -> Brand | None:
        return self.db.execute(select(Brand).where(Brand.name == name)).scalars().first()

    def add(self, brand: Brand) -> Brand:
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def update(self, brand: Brand) -> Brand:
        self.db.commit()
        self.db.refresh(brand)
        return brand
