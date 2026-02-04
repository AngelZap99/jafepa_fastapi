from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from src.shared.database.dependencies import SessionDep
from src.modules.product.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductStockResponse,
    InventoryStockItem,
)
from src.modules.product.domain.product_service import ProductService
from src.modules.product.domain.product_repository import ProductRepository
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.product.product_model import Product
from src.shared.models.warehouse.warehouse_model import Warehouse

from collections import defaultdict

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


@router.get("/list-stock", response_model=list[ProductStockResponse])
def list_products_with_stock(
    warehouse_id: int,
    session: SessionDep,
    search: str | None = None,
    only_in_stock: bool = False,
    include_inactive: bool = True,
    skip: int = 0,
    limit: int = 100,
):
    """
    BFF endpoint for Sales UI:
    returns products + their inventory entries (and total stock) for a given warehouse.
    """
    warehouse = session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    inv_base_q = session.query(Inventory).filter(Inventory.warehouse_id == warehouse_id)
    if not include_inactive:
        inv_base_q = inv_base_q.filter(Inventory.is_active == True)  # noqa: E712

    product_ids_subq = inv_base_q.with_entities(Inventory.product_id).distinct().subquery()

    q = session.query(Product).filter(Product.id.in_(product_ids_subq)).order_by(Product.id)
    if not include_inactive:
        q = q.filter(Product.is_active == True)  # noqa: E712
    if search:
        s = f"%{search.strip()}%"
        q = q.filter((Product.name.ilike(s)) | (Product.code.ilike(s)))

    products = q.offset(skip).limit(limit).all()
    if not products:
        return []

    product_ids = [p.id for p in products]
    inventories = inv_base_q.filter(Inventory.product_id.in_(product_ids)).all()

    inv_map: dict[int, list[Inventory]] = defaultdict(list)
    for inv in inventories:
        inv_map[inv.product_id].append(inv)

    out: list[ProductStockResponse] = []
    for product in products:
        inv_items = inv_map.get(product.id, [])
        stock_total = sum(i.stock for i in inv_items if include_inactive or i.is_active)
        if only_in_stock and stock_total <= 0:
            continue

        base = ProductResponse.model_validate(product, from_attributes=True)
        out.append(
            ProductStockResponse(
                **base.model_dump(),
                stock_total=stock_total,
                inventory=[
                    InventoryStockItem.model_validate(i, from_attributes=True)
                    for i in inv_items
                ],
            )
        )

    return out


@router.get("/{product_id:int}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return service.get_product(product_id)
