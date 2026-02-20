# src/modules/category/domain/category_service.py

from typing import List
from fastapi import HTTPException, status

from src.shared.models.category.category_model import Category
from src.modules.category.category_schema import (
    CategoryCreate,
    CategoryUpdate,
)
from src.modules.category.domain.category_repository import CategoryRepository
import datetime
class CategoryService:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    def _get_category_or_404(self, category_id: int) -> Category:
        category = self.repository.get(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category

    def _ensure_name_not_taken(
        self,
        name: str,
        parent_id: int | None,
        category_owner_id: int | None = None,
    ) -> None:
        """
        Evita duplicados: no se puede repetir el nombre dentro del mismo parent_id.
        """
        existing = self.repository.get_by_name_and_parent(name, parent_id)

        if existing and (category_owner_id is None or existing.id != category_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{name}' already exists under this parent.",
            )

    def list_categories(self, skip: int = 0, limit: int | None = None) -> List[Category]:
        # By default, list should include inactive records too.
        return self.repository.list(skip=skip, limit=limit)

    def get_category(self, category_id: int) -> Category:
        return self._get_category_or_404(category_id)

    def create_category(self, payload: CategoryCreate) -> Category:
        self._ensure_name_not_taken(payload.name, payload.parent_id)

        category = Category(
            parent_id=payload.parent_id,
            name=payload.name,
            description=payload.description,
            is_active=True,
        )

        return self.repository.add(category)

    def update_category(self, category_id: int, payload: CategoryUpdate) -> Category:
        category = self._get_category_or_404(category_id)
        data = payload.model_dump(exclude_unset=True)
        print(payload.model_dump())
        # Validar nombre solo si se actualiza
        if "name" in data:
            new_name = data["name"]
            new_parent_id = data.get("parent_id", category.parent_id)

            self._ensure_name_not_taken(
                new_name,
                new_parent_id,
                category_owner_id=category.id,
            )

        # Aplicar cambios al modelo
        for field, value in data.items():
            setattr(category, field, value)

        return self.repository.update(category)

    def delete_category(self, category_id: int) -> Category:
        category = self._get_category_or_404(category_id)
        category.is_active = False
        category.deleted_at = datetime.datetime.utcnow()
        return self.repository.update(category)
