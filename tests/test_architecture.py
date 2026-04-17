from pathlib import Path

from src.modules.auth.auth_dependencies import get_current_user
from src.modules.bff.bff_router import router as bff_router
from src.modules.brand.brand_router import router as brand_router
from src.modules.category.category_router import router as category_router
from src.modules.client.client_router import router as client_router
from src.modules.invoice.invoice_router import router as invoice_router
from src.modules.invoice_line.invoice_line_router import router as invoice_line_router
from src.modules.inventory.inventory_router import router as inventory_router
from src.modules.product.product_router import router as product_router
from src.modules.sale.sale_router import router as sale_router
from src.modules.users.users_router import router as users_router
from src.modules.warehouse.warehouse_router import router as warehouse_router


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
ALLOWED_JSON_RESPONSE_FILES = {
    SRC_ROOT / "shared" / "exception_handlers.py",
}
PROTECTED_ROUTERS = {
    "users": users_router,
    "clients": client_router,
    "warehouses": warehouse_router,
    "categories": category_router,
    "brands": brand_router,
    "products": product_router,
    "invoices": invoice_router,
    "invoice_lines": invoice_line_router,
    "inventory": inventory_router,
    "sales": sale_router,
    "bff": bff_router,
}


def test_jsonresponse_is_only_used_in_global_exception_handlers():
    offenders: list[str] = []

    for path in SRC_ROOT.rglob("*.py"):
        if path in ALLOWED_JSON_RESPONSE_FILES:
            continue

        if "JSONResponse(" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []


def test_business_routers_require_authenticated_user():
    offenders: list[str] = []

    for name, router in PROTECTED_ROUTERS.items():
        dependencies = [dependency.dependency for dependency in router.dependencies]
        if get_current_user not in dependencies:
            offenders.append(name)

    assert offenders == []
