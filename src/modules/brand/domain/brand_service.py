from typing import List
from fastapi import HTTPException, status

from src.shared.models.brand.brand_model import Brand
from src.modules.brand.brand_schema import BrandCreate, BrandUpdate
from src.modules.brand.domain.brand_repository import BrandRepository
import datetime

class BrandService:
    def __init__(self, repository: BrandRepository) -> None:
        self.repository = repository

    def _ensure_name_not_taken(
        self, name: str, brand_owner_id: int | None = None
    ) -> None:
        existing = self.repository.get_by_name(name)

        if existing and (brand_owner_id is None or existing.id != brand_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand '{name}' already exists",
            )

    def _get_brand_or_404(self, brand_id: int) -> Brand:
        brand = self.repository.get(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found",
            )
        return brand

    def list_brands(self, skip: int = 0, limit: int = 100) -> List[Brand]:
        # Solo marcas activas (deleted_at es None)
        all_brands = self.repository.list(skip=skip, limit=limit)
        return [brand for brand in all_brands if brand.deleted_at is None]

    def get_brand(self, brand_id: int) -> Brand:
        return self._get_brand_or_404(brand_id)

    def create_brand(self, payload: BrandCreate) -> Brand:
        self._ensure_name_not_taken(payload.name)

        brand = Brand(
            name=payload.name,
        )

        return self.repository.add(brand)

    def update_brand(self, brand_id: int, payload: BrandUpdate) -> Brand:
        brand = self._get_brand_or_404(brand_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data:
            self._ensure_name_not_taken(data["name"], brand_owner_id=brand.id)

        for field, value in data.items():
            setattr(brand, field, value)

        return self.repository.update(brand)

    def delete_brand(self, brand_id: int) -> Brand:
        brand = self._get_brand_or_404(brand_id)
        brand.deleted_at = datetime.datetime.utcnow()
        brand.is_active = False

        return self.repository.update(brand)
