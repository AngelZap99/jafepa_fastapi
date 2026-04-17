from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from src.modules.bff.bff_schema import (
    CatalogCounts,
    InvoiceStatusCounts,
    SaleStatusCounts,
    SystemSummaryResponse,
)
from src.shared.database.dependencies import SessionDep
from src.shared.enums.invoice_enums import InvoiceStatus
from src.shared.enums.sale_enums import SaleStatus
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.client.client_model import Client
from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.product.product_model import Product
from src.shared.models.sale.sale_model import Sale
from src.shared.models.user.user_model import User
from src.shared.models.warehouse.warehouse_model import Warehouse
from src.shared.utils.datetime import utcnow
from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/bff",
    tags=["bff"],
    dependencies=[Depends(get_current_user)],
)


def _count(session: SessionDep, model, *filters) -> int:
    stmt = select(func.count(model.id))
    if filters:
        stmt = stmt.where(*filters)
    result = session.exec(stmt).one()
    return int(result or 0)


@router.get(
    "/system-summary",
    response_model=SystemSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_system_summary(
    session: SessionDep,
    days: int = Query(
        14,
        ge=1,
        le=365,
        description="Window in days for recent ARRIVED invoices and PAID sales.",
    ),
):
    cutoff = date.today() - timedelta(days=days)

    catalogs = CatalogCounts(
        products=_count(session, Product, Product.is_active == True),  # noqa: E712
        clients=_count(session, Client, Client.is_active == True),  # noqa: E712
        warehouses=_count(session, Warehouse, Warehouse.is_active == True),  # noqa: E712
        users=_count(session, User, User.is_active == True),  # noqa: E712
        categories=_count(session, Category, Category.is_active == True),  # noqa: E712
        brands=_count(session, Brand, Brand.is_active == True),  # noqa: E712
    )

    invoice_date_for_window = func.coalesce(Invoice.arrival_date, Invoice.invoice_date)
    invoices = InvoiceStatusCounts(
        pending=_count(
            session,
            Invoice,
            Invoice.is_active == True,  # noqa: E712
            Invoice.status == InvoiceStatus.DRAFT,
        ),
        cancelled=_count(
            session,
            Invoice,
            Invoice.is_active == True,  # noqa: E712
            Invoice.status == InvoiceStatus.CANCELLED,
        ),
        arrived_last_n_days=_count(
            session,
            Invoice,
            Invoice.is_active == True,  # noqa: E712
            Invoice.status == InvoiceStatus.ARRIVED,
            invoice_date_for_window >= cutoff,
        ),
    )

    sales = SaleStatusCounts(
        pending=_count(
            session,
            Sale,
            Sale.is_active == True,  # noqa: E712
            Sale.status == SaleStatus.DRAFT,
        ),
        cancelled=_count(
            session,
            Sale,
            Sale.is_active == True,  # noqa: E712
            Sale.status == SaleStatus.CANCELLED,
        ),
        paid_last_n_days=_count(
            session,
            Sale,
            Sale.is_active == True,  # noqa: E712
            Sale.status == SaleStatus.PAID,
            Sale.sale_date >= cutoff,
        ),
    )

    return SystemSummaryResponse(
        days=days,
        cutoff_date=cutoff,
        generated_at=utcnow(),
        catalogs=catalogs,
        invoices=invoices,
        sales=sales,
    )
