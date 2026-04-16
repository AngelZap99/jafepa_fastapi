# src/modules/category/domain/category_repository.py

from sqlalchemy.orm import Session
from src.shared.models.category.category_model import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, category_id: int) -> Category | None:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Category | None:
        return self.db.query(Category).filter(Category.name == name).first()

    def list(self, skip: int = 0, limit: int | None = None) -> list[Category]:
        q = self.db.query(Category).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def add(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
