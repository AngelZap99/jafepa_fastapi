from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from src.shared.database.dependencies import SessionDep
from src.modules.product.product_schema import ProductCreate, ProductUpdate, ProductResponse
from src.modules.product.domain.product_service import ProductService
from src.modules.product.domain.product_repository import ProductRepository

router = APIRouter(
    prefix="/products",
    tags=["products"],
)

def get_product_service(session: SessionDep) -> ProductService:
    repository = ProductRepository(session)
    return ProductService(repository)

@router.get("/list", response_model=list[ProductResponse])
def list_products(service: ProductService = Depends(get_product_service)):
    return service.list_products()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return service.get_product(product_id)

@router.post("/create", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate = Depends(ProductCreate.as_form),
    image_file: UploadFile | None = File(None),
    service: ProductService = Depends(get_product_service),
):
    try:
        return service.create_product(payload, image=image_file)
    except HTTPException as e:
        if e.status_code == 409:
            return JSONResponse(status_code=409, content={"errors": e.detail})
        raise e

@router.put("/update/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate = Depends(ProductUpdate.as_form),
    image_file: UploadFile | None = File(None),
    service: ProductService = Depends(get_product_service),
):
    try:
        return service.update_product(product_id, payload, image=image_file)
    except HTTPException as e:
        if e.status_code == 409:
            return JSONResponse(status_code=409, content={"errors": e.detail})
        if e.status_code == 404:
            return JSONResponse(status_code=404, content={"error": e.detail})
        raise e

@router.delete("/delete/{product_id}", response_model=ProductResponse)
def delete_product(product_id: int, service: ProductService = Depends(get_product_service)):
    try:
        return service.delete_product(product_id)
    except HTTPException as e:
        if e.status_code == 404:
            return JSONResponse(status_code=404, content={"error": e.detail})
        raise e
