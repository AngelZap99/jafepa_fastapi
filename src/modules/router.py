from fastapi import APIRouter

from src.modules.users.users_router import router as users_router
from src.modules.auth.auth_router import router as auth_router
from src.modules.client.client_router import router as client_router
from src.modules.warehouse.warehouse_router import router as warehouse_router
from src.modules.category.category_router import router as category_router
from src.modules.brand.brand_router import router as brand_router
from src.modules.product.product_router import router as product_router
from src.modules.invoice.invoice_router import router as invoice_router
from src.modules.invoice_line.invoice_line_router import router as invoice_line_router
from src.modules.inventory.inventory_router import router as inventory_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(client_router)
api_router.include_router(warehouse_router)
api_router.include_router(category_router)
api_router.include_router(brand_router)
api_router.include_router(product_router)
api_router.include_router(invoice_router)
api_router.include_router(invoice_line_router)
api_router.include_router(inventory_router)
