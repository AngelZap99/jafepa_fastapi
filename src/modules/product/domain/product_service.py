from typing import List
from fastapi import HTTPException, status

from src.shared.models.product.product_model import Product
from src.modules.product.product_schema import ProductCreate, ProductUpdate
from src.modules.product.domain.product_repository import ProductRepository


class ProductService:

    ####################
    # Private methods
    ####################
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    def _ensure_code_not_taken(
        self, code: str, product_owner_id: int | None = None
    ) -> None:
        existing = self.repository.get_by_code(code)

        # Si existe otro producto con ese código → error
        if existing and (product_owner_id is None or existing.id != product_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product code {code} is already taken",
            )

    def _get_product_or_404(self, product_id: int) -> Product:
        product = self.repository.get(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    ####################
    # Public methods
    ####################
    def list_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.repository.list(skip=skip, limit=limit)

    def get_product(self, product_id: int) -> Product:
        return self._get_product_or_404(product_id)

    def create_product(self, payload: ProductCreate) -> Product:
        # Validar código único
        self._ensure_code_not_taken(payload.code)

        product = Product(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            category_id=payload.category_id,
            subcategory_id=payload.subcategory_id,
            brand_id=payload.brand_id,
            image=payload.image,
            is_active=True,
        )

        return self.repository.add(product)

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self._get_product_or_404(product_id)
        data = payload.model_dump(exclude_unset=True)

        # ¿Se actualiza el código?
        if "code" in data:
            self._ensure_code_not_taken(data["code"], product_owner_id=product.id)

        # Aplicar los cambios al modelo
        for field, value in data.items():
            setattr(product, field, value)

        return self.repository.update(product)

    def delete_product(self, product_id: int) -> Product:
        product = self._get_product_or_404(product_id)
        product.is_active = False
        self.repository.update(product)
        return product
