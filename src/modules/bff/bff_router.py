from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, case, extract, func, select

from src.modules.bff.bff_schema import (
    CatalogCounts,
    InventoryHealthCounts,
    InvoiceStatusCounts,
    MonthlySalesPoint,
    ProductFlowAnalysisItem,
    ProductFlowAnalysisResponse,
    ProductFlowItem,
    ProductFlowSummary,
    SaleStatusCounts,
    SystemSummaryResponse,
)
from src.shared.database.dependencies import SessionDep
from src.shared.enums.invoice_enums import InvoiceStatus
from src.shared.enums.sale_enums import SaleLineQuantityMode, SaleStatus
from src.shared.models.brand.brand_model import Brand
from src.shared.models.category.category_model import Category
from src.shared.models.client.client_model import Client
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.invoice.invoice_model import Invoice
from src.shared.models.product.product_model import Product
from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.models.user.user_model import User
from src.shared.models.warehouse.warehouse_model import Warehouse
from src.shared.utils.datetime import utcnow
from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/bff",
    tags=["bff"],
    dependencies=[Depends(get_current_user)],
)


def _row_mapping(row) -> dict:
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, offset: int) -> date:
    absolute_month = value.year * 12 + value.month - 1 + offset
    return date(absolute_month // 12, absolute_month % 12 + 1, 1)


def _catalog_counts(session: SessionDep) -> CatalogCounts:
    statement = select(
        select(func.count(Product.id))
        .where(Product.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("products"),
        select(func.count(Client.id))
        .where(Client.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("clients"),
        select(func.count(Warehouse.id))
        .where(Warehouse.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("warehouses"),
        select(func.count(User.id))
        .where(User.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("users"),
        select(func.count(Category.id))
        .where(Category.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("categories"),
        select(func.count(Brand.id))
        .where(Brand.is_active == True)  # noqa: E712
        .scalar_subquery()
        .label("brands"),
    )
    return CatalogCounts(**_row_mapping(session.exec(statement).one()))


def _sale_counts(
    session: SessionDep,
    *,
    cutoff: date,
    today: date,
) -> SaleStatusCounts:
    paid_in_period = and_(
        Sale.is_active == True,  # noqa: E712
        Sale.status == SaleStatus.PAID,
        Sale.sale_date >= cutoff,
        Sale.sale_date <= today,
    )
    cancelled_in_period = and_(
        Sale.is_active == True,  # noqa: E712
        Sale.status == SaleStatus.CANCELLED,
        Sale.sale_date >= cutoff,
        Sale.sale_date <= today,
    )
    statement = select(
        func.coalesce(func.sum(case((paid_in_period, 1), else_=0)), 0).label(
            "paid_last_n_days"
        ),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Sale.is_active == True,  # noqa: E712
                            Sale.status == SaleStatus.DRAFT,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("pending"),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Sale.is_active == True,  # noqa: E712
                            Sale.status == SaleStatus.CANCELLED,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("cancelled"),
        func.coalesce(
            func.sum(case((cancelled_in_period, 1), else_=0)), 0
        ).label("cancelled_last_n_days"),
        func.coalesce(
            func.sum(case((paid_in_period, Sale.total_price), else_=Decimal("0"))),
            Decimal("0"),
        ).label("revenue_last_n_days"),
    )
    values = _row_mapping(session.exec(statement).one())
    paid_count = int(values["paid_last_n_days"] or 0)
    revenue = Decimal(values["revenue_last_n_days"] or 0).quantize(
        Decimal("0.01")
    )
    average_ticket = (
        (revenue / Decimal(paid_count)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if paid_count
        else Decimal("0.00")
    )
    return SaleStatusCounts(
        paid_last_n_days=paid_count,
        pending=int(values["pending"] or 0),
        cancelled=int(values["cancelled"] or 0),
        cancelled_last_n_days=int(values["cancelled_last_n_days"] or 0),
        revenue_last_n_days=revenue,
        average_ticket_last_n_days=average_ticket,
    )


def _invoice_counts(
    session: SessionDep,
    *,
    cutoff: date,
    today: date,
) -> InvoiceStatusCounts:
    invoice_date_for_window = func.coalesce(
        Invoice.arrival_date, Invoice.invoice_date
    )
    arrived_in_period = and_(
        Invoice.is_active == True,  # noqa: E712
        Invoice.status == InvoiceStatus.ARRIVED,
        invoice_date_for_window >= cutoff,
        invoice_date_for_window <= today,
    )
    cancelled_in_period = and_(
        Invoice.is_active == True,  # noqa: E712
        Invoice.status == InvoiceStatus.CANCELLED,
        Invoice.invoice_date >= cutoff,
        Invoice.invoice_date <= today,
    )
    statement = select(
        func.coalesce(
            func.sum(case((arrived_in_period, 1), else_=0)), 0
        ).label("arrived_last_n_days"),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Invoice.is_active == True,  # noqa: E712
                            Invoice.status == InvoiceStatus.DRAFT,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("pending"),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Invoice.is_active == True,  # noqa: E712
                            Invoice.status == InvoiceStatus.CANCELLED,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("cancelled"),
        func.coalesce(
            func.sum(case((cancelled_in_period, 1), else_=0)), 0
        ).label("cancelled_last_n_days"),
    )
    values = _row_mapping(session.exec(statement).one())
    return InvoiceStatusCounts(
        pending=int(values["pending"] or 0),
        cancelled=int(values["cancelled"] or 0),
        arrived_last_n_days=int(values["arrived_last_n_days"] or 0),
        cancelled_last_n_days=int(values["cancelled_last_n_days"] or 0),
    )


def _inventory_health(session: SessionDep) -> InventoryHealthCounts:
    available_units = case(
        (
            Inventory.stock > Inventory.reserved_stock,
            (Inventory.stock - Inventory.reserved_stock) * Inventory.box_size,
        ),
        else_=0,
    )
    availability_by_product = (
        select(
            Inventory.product_id.label("product_id"),
            func.coalesce(func.sum(available_units), 0).label("available_units"),
        )
        .where(Inventory.is_active == True)  # noqa: E712
        .group_by(Inventory.product_id)
        .subquery()
    )
    statement = (
        select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            func.coalesce(
                                availability_by_product.c.available_units, 0
                            )
                            > 0,
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("products_with_availability"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            func.coalesce(
                                availability_by_product.c.available_units, 0
                            )
                            <= 0,
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("products_without_availability"),
            select(func.count(Inventory.id))
            .where(
                Inventory.is_active == True,  # noqa: E712
                Inventory.reserved_stock > Inventory.stock,
            )
            .scalar_subquery()
            .label("over_reserved_inventories"),
        )
        .select_from(Product)
        .outerjoin(
            availability_by_product,
            availability_by_product.c.product_id == Product.id,
        )
        .where(Product.is_active == True)  # noqa: E712
    )
    values = _row_mapping(session.exec(statement).one())
    return InventoryHealthCounts(
        products_with_availability=int(values["products_with_availability"] or 0),
        products_without_availability=int(
            values["products_without_availability"] or 0
        ),
        over_reserved_inventories=int(values["over_reserved_inventories"] or 0),
    )


def _normalized_units_expression():
    return case(
        (
            SaleLine.quantity_mode == SaleLineQuantityMode.BOX,
            SaleLine.quantity_units * SaleLine.box_size,
        ),
        else_=SaleLine.quantity_units,
    )


def _load_product_flow_items(
    session: SessionDep,
    *,
    from_date: date,
    to_date: date,
) -> list[ProductFlowItem]:
    normalized_units = _normalized_units_expression()
    aggregates = (
        select(
            Inventory.product_id.label("product_id"),
            func.coalesce(func.sum(normalized_units), 0).label("units_sold"),
            func.count(func.distinct(Sale.id)).label("sales_count"),
            func.coalesce(func.sum(SaleLine.total_price), Decimal("0")).label(
                "total_amount"
            ),
        )
        .select_from(SaleLine)
        .join(Sale, Sale.id == SaleLine.sale_id)
        .join(Inventory, Inventory.id == SaleLine.inventory_id)
        .where(
            Sale.is_active == True,  # noqa: E712
            SaleLine.is_active == True,  # noqa: E712
            Sale.status == SaleStatus.PAID,
            Sale.sale_date >= from_date,
            Sale.sale_date <= to_date,
        )
        .group_by(Inventory.product_id)
        .subquery()
    )
    statement = (
        select(
            Product.id.label("product_id"),
            Product.code.label("product_code"),
            Product.name.label("product_name"),
            func.coalesce(aggregates.c.units_sold, 0).label("units_sold"),
            func.coalesce(aggregates.c.sales_count, 0).label("sales_count"),
            func.coalesce(aggregates.c.total_amount, Decimal("0")).label(
                "total_amount"
            ),
        )
        .outerjoin(aggregates, aggregates.c.product_id == Product.id)
        .where(Product.is_active == True)  # noqa: E712
    )
    items: list[ProductFlowItem] = []
    for row in session.exec(statement).all():
        values = _row_mapping(row)
        units_sold = int(values["units_sold"] or 0)
        sales_count = int(values["sales_count"] or 0)
        average_units = (
            (Decimal(units_sold) / Decimal(sales_count)).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
            if sales_count
            else Decimal("0.0")
        )
        items.append(
            ProductFlowItem(
                product_id=int(values["product_id"]),
                product_code=values["product_code"],
                product_name=values["product_name"],
                units_sold=units_sold,
                sales_count=sales_count,
                total_amount=Decimal(values["total_amount"] or 0).quantize(
                    Decimal("0.01")
                ),
                average_units_per_sale=average_units,
            )
        )

    return items


def _product_flow(
    session: SessionDep,
    *,
    from_date: date,
    to_date: date,
    months: int,
) -> ProductFlowSummary:
    items = _load_product_flow_items(
        session,
        from_date=from_date,
        to_date=to_date,
    )
    top_products = sorted(
        (item for item in items if item.units_sold > 0),
        key=lambda item: (
            -item.units_sold,
            -item.total_amount,
            item.product_name.lower(),
        ),
    )[:5]
    low_products = sorted(
        items,
        key=lambda item: (
            item.units_sold,
            item.total_amount,
            item.product_name.lower(),
        ),
    )[:5]
    return ProductFlowSummary(
        months=months,
        from_date=from_date,
        to_date=to_date,
        products_without_sales=sum(item.units_sold == 0 for item in items),
        top_products=top_products,
        low_products=low_products,
    )


def _competition_rank(values: list[Decimal | int], current: Decimal | int) -> int:
    return 1 + sum(value > current for value in values)


def _lower_value_percentile(
    values: list[Decimal | int],
    current: Decimal | int,
) -> Decimal:
    if not values or max(values) == min(values):
        return Decimal("100.0") if current > 0 else Decimal("0.0")
    lower_count = sum(value < current for value in values)
    return (
        Decimal(lower_count) * Decimal("100") / Decimal(len(values) - 1)
    ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _analyze_product_flow(
    items: list[ProductFlowItem],
) -> list[ProductFlowAnalysisItem]:
    sales_values = [item.sales_count for item in items]
    unit_values = [item.units_sold for item in items]
    scored_items = []

    for item in items:
        frequency_percentile = _lower_value_percentile(
            sales_values,
            item.sales_count,
        )
        volume_percentile = _lower_value_percentile(
            unit_values,
            item.units_sold,
        )
        mixed_score = (
            (frequency_percentile + volume_percentile) / Decimal("2")
        ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        scored_items.append(
            {
                "item": item,
                "frequency_percentile": frequency_percentile,
                "volume_percentile": volume_percentile,
                "mixed_score": mixed_score,
            }
        )

    mixed_values = [entry["mixed_score"] for entry in scored_items]
    return [
        ProductFlowAnalysisItem(
            **entry["item"].model_dump(),
            sales_rank=_competition_rank(sales_values, entry["item"].sales_count),
            units_rank=_competition_rank(unit_values, entry["item"].units_sold),
            mixed_rank=_competition_rank(mixed_values, entry["mixed_score"]),
            frequency_percentile=entry["frequency_percentile"],
            volume_percentile=entry["volume_percentile"],
            mixed_score=entry["mixed_score"],
        )
        for entry in scored_items
    ]


def _monthly_sales(
    session: SessionDep,
    *,
    from_date: date,
    to_date: date,
    months: int,
) -> list[MonthlySalesPoint]:
    normalized_units = _normalized_units_expression()
    year = extract("year", Sale.sale_date)
    month = extract("month", Sale.sale_date)
    statement = (
        select(
            year.label("year"),
            month.label("month"),
            func.count(func.distinct(Sale.id)).label("sales_count"),
            func.coalesce(func.sum(normalized_units), 0).label("units_sold"),
            func.coalesce(func.sum(SaleLine.total_price), Decimal("0")).label(
                "total_amount"
            ),
        )
        .select_from(SaleLine)
        .join(Sale, Sale.id == SaleLine.sale_id)
        .where(
            Sale.is_active == True,  # noqa: E712
            SaleLine.is_active == True,  # noqa: E712
            Sale.status == SaleStatus.PAID,
            Sale.sale_date >= from_date,
            Sale.sale_date <= to_date,
        )
        .group_by(year, month)
    )
    values_by_month = {}
    for row in session.exec(statement).all():
        values = _row_mapping(row)
        values_by_month[(int(values["year"]), int(values["month"]))] = values

    points = []
    current_month = _month_start(from_date)
    for offset in range(months):
        month_date = _shift_month(current_month, offset)
        values = values_by_month.get((month_date.year, month_date.month), {})
        points.append(
            MonthlySalesPoint(
                month=month_date.strftime("%Y-%m"),
                sales_count=int(values.get("sales_count") or 0),
                units_sold=int(values.get("units_sold") or 0),
                total_amount=Decimal(values.get("total_amount") or 0).quantize(
                    Decimal("0.01")
                ),
            )
        )
    return points


@router.get(
    "/product-flow",
    response_model=ProductFlowAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def get_product_flow_analysis(
    session: SessionDep,
    months: int = Query(default=6, ge=1, le=12),
    search: str | None = Query(default=None, max_length=100),
    sort_by: Literal["sales", "units", "mixed"] = Query(default="mixed"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=50),
):
    today = date.today()
    from_date = _shift_month(_month_start(today), -(months - 1))
    all_items = _analyze_product_flow(
        _load_product_flow_items(
            session,
            from_date=from_date,
            to_date=today,
        )
    )

    normalized_search = search.strip().casefold() if search else ""
    filtered_items = [
        item
        for item in all_items
        if not normalized_search
        or normalized_search in item.product_code.casefold()
        or normalized_search in item.product_name.casefold()
    ]

    filtered_items.sort(key=lambda item: item.product_name.casefold())
    if sort_by == "sales":
        metric = lambda item: (  # noqa: E731
            item.sales_count,
            item.units_sold,
            item.total_amount,
        )
    elif sort_by == "units":
        metric = lambda item: (  # noqa: E731
            item.units_sold,
            item.sales_count,
            item.total_amount,
        )
    else:
        metric = lambda item: (  # noqa: E731
            item.mixed_score,
            item.sales_count,
            item.units_sold,
        )
    filtered_items.sort(key=metric, reverse=order == "desc")

    return ProductFlowAnalysisResponse(
        months=months,
        from_date=from_date,
        to_date=today,
        search=search.strip() if search and search.strip() else None,
        sort_by=sort_by,
        order=order,
        products_without_sales=sum(item.units_sold == 0 for item in all_items),
        items=filtered_items[skip : skip + limit],
        total=len(filtered_items),
        skip=skip,
        limit=limit,
    )


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
    flow_months: int = Query(
        6,
        ge=1,
        le=12,
        description="Calendar months used for product flow and sales trend.",
    ),
):
    today = date.today()
    cutoff = today - timedelta(days=days - 1)
    flow_cutoff = _shift_month(_month_start(today), -(flow_months - 1))

    return SystemSummaryResponse(
        days=days,
        cutoff_date=cutoff,
        generated_at=utcnow(),
        catalogs=_catalog_counts(session),
        invoices=_invoice_counts(
            session,
            cutoff=cutoff,
            today=today,
        ),
        sales=_sale_counts(
            session,
            cutoff=cutoff,
            today=today,
        ),
        inventory=_inventory_health(session),
        product_flow=_product_flow(
            session,
            from_date=flow_cutoff,
            to_date=today,
            months=flow_months,
        ),
        monthly_sales=_monthly_sales(
            session,
            from_date=flow_cutoff,
            to_date=today,
            months=flow_months,
        ),
    )
