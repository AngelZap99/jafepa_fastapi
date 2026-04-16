from typing import List, Optional

from fastapi import HTTPException, UploadFile, status

from src.shared.models.product.product_model import Product
from src.modules.product.product_schema import ProductCreate, ProductUpdate
from src.modules.product.domain.product_repository import ProductRepository

from src.shared.files.image_validator import ImageValidator
from src.shared.files.upload_file_s3 import S3FileHandler


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository
        self.image_validator = ImageValidator()
        self._s3: S3FileHandler | None = None

    def _get_s3(self) -> S3FileHandler:
        if self._s3 is None:
            self._s3 = S3FileHandler()
        return self._s3

    def _get_product_or_404(self, product_id: int) -> Product:
        product = self.repository.get(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    def _upload_one_product_image(
        self, product_id: int, image: UploadFile
    ) -> tuple[str, str]:
        self.image_validator.validate(
            [image],
            max_size_bytes=5 * 1024 * 1024,
            allowed_extensions={".jpg", ".jpeg", ".png", ".webp"},
            allowed_mime_types={"image/jpeg", "image/png", ".webp"},
            require_magic_bytes=True,
        )
        return self._get_s3().upload_uploadfile(
            image,
            prefix=f"PRODUCT_IMAGES/{product_id}",
            make_public=True,
        )

    def list_products(self, skip: int = 0, limit: Optional[int] = None) -> List[Product]:
        return self.repository.list(skip=skip, limit=limit)

    def get_product(self, product_id: int) -> Product:
        return self._get_product_or_404(product_id)

    def create_product(
        self, payload: ProductCreate, image: Optional[UploadFile] = None
    ) -> Product:
        # Verificar conflictos
        conflicts = self.repository.check_conflicts(payload)
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflicts,
            )

        product = Product(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            image=payload.image,
            is_active=True,
        )

        product = self.repository.add(product)

        if image:
            key = None
            try:
                key, url = self._upload_one_product_image(product.id, image)
                product.image = url
                product = self.repository.update(product)
            except Exception:
                if key:
                    self._get_s3().delete_file(key)
                raise

        return product

    def update_product(
        self,
        product_id: int,
        payload: ProductUpdate,
        image: Optional[UploadFile] = None,
    ) -> Product:
        product = self._get_product_or_404(product_id)
        data = payload.model_dump(exclude_unset=True)

        # Verificar conflictos
        conflicts = self.repository.check_conflicts(payload, product_id=product.id)
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflicts,
            )

        for field, value in data.items():
            if value is not None:
                setattr(product, field, value)

        if image:
            old_image = product.image
            key = None
            try:
                key, url = self._upload_one_product_image(product.id, image)
                product.image = url
                product = self.repository.update(product)
            except Exception:
                if key:
                    self._get_s3().delete_file(key)
                raise

            if old_image:
                self._get_s3().delete_file(old_image)

        return self.repository.update(product)

    def delete_product(self, product_id: int) -> Product:
        product = self._get_product_or_404(product_id)
        product.is_active = False
        return self.repository.update(product)
