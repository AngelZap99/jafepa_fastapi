from collections import defaultdict

from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import select

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
from src.modules.inventory.domain.inventory_movement_repository import (
    InventoryMovementRepository,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def get_product_service(session: SessionDep) -> ProductService:
    repository = ProductRepository(session)
    return ProductService(repository)


@router.get("/list", response_model=list[ProductResponse])
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    service: ProductService = Depends(get_product_service),
):
    return service.list_products(skip=skip, limit=limit)

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
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
):
    """
    BFF endpoint for Sales UI:
    returns products + their inventory entries (and total stock) for a given warehouse.
    """
    warehouse = session.exec(select(Warehouse).where(Warehouse.id == warehouse_id)).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    inv_base_q = select(Inventory).where(Inventory.warehouse_id == warehouse_id)
    if not include_inactive:
        inv_base_q = inv_base_q.where(Inventory.is_active == True)  # noqa: E712

    product_ids_stmt = (
        select(Inventory.product_id)
        .where(Inventory.warehouse_id == warehouse_id)
        .distinct()
    )
    if not include_inactive:
        product_ids_stmt = product_ids_stmt.where(Inventory.is_active == True)  # noqa: E712

    q = select(Product).where(Product.id.in_(product_ids_stmt)).order_by(Product.id)
    if not include_inactive:
        q = q.where(Product.is_active == True)  # noqa: E712
    if search:
        s = f"%{search.strip()}%"
        q = q.where((Product.name.ilike(s)) | (Product.code.ilike(s)))

    q = q.offset(skip)
    if limit is not None:
        q = q.limit(limit)
    products = list(session.exec(q).all())
    if not products:
        return []

    product_ids = [p.id for p in products]
    inventories = list(
        session.exec(inv_base_q.where(Inventory.product_id.in_(product_ids))).all()
    )
    movement_repo = InventoryMovementRepository(session)
    metrics_window_months = 12

    inv_map: dict[int, list[Inventory]] = defaultdict(list)
    for inv in inventories:
        inv_map[inv.product_id].append(inv)

    out: list[ProductStockResponse] = []
    for product in products:
        inv_items = inv_map.get(product.id, [])
        stock_total = sum(i.stock for i in inv_items if include_inactive or i.is_active)
        stock_boxes_total = stock_total
        if only_in_stock and stock_boxes_total <= 0:
            continue

        base = ProductResponse.model_validate(product, from_attributes=True)
        inventory_payload = []
        for inv in inv_items:
            if not include_inactive and not inv.is_active:
                continue

            available_boxes = inv.stock
            recent_qty, recent_cost = movement_repo.get_recent_out_totals(
                inv.id, months=metrics_window_months
            )
            sales_avg_price = (
                float(recent_cost / recent_qty) if recent_qty > 0 else None
            )
            sales_last_price = movement_repo.get_latest_out_unit_cost(
                inv.id, months=metrics_window_months
            )
            item_data = InventoryStockItem.model_validate(inv, from_attributes=True).model_dump()
            item_data.update(
                {
                    "available_boxes": available_boxes,
                    "sales_last_price": float(sales_last_price)
                    if sales_last_price is not None
                    else None,
                    "sales_avg_price": sales_avg_price,
                }
            )
            inventory_payload.append(InventoryStockItem(**item_data))

        out.append(
            ProductStockResponse(
                **base.model_dump(),
                stock_total=stock_total,
                stock_boxes_total=stock_boxes_total,
                inventory=inventory_payload,
            )
        )

    return out


@router.get("/{product_id:int}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return service.get_product(product_id)
