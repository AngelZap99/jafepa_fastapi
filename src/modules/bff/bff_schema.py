from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from src.shared.schemas.datetime_types import UTCDateTime


class CatalogCounts(BaseModel):
    products: int
    clients: int
    warehouses: int
    users: int

    categories: int
    brands: int


class InvoiceStatusCounts(BaseModel):
    pending: int
    cancelled: int
    arrived_last_n_days: int
    cancelled_last_n_days: int = 0


class SaleStatusCounts(BaseModel):
    pending: int
    cancelled: int
    paid_last_n_days: int
    cancelled_last_n_days: int = 0
    revenue_last_n_days: Decimal = Decimal("0.00")
    average_ticket_last_n_days: Decimal = Decimal("0.00")


class InventoryHealthCounts(BaseModel):
    products_with_availability: int
    products_without_availability: int
    over_reserved_inventories: int


class ProductFlowItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    units_sold: int
    sales_count: int
    total_amount: Decimal
    average_units_per_sale: Decimal


class ProductFlowAnalysisItem(ProductFlowItem):
    sales_rank: int
    units_rank: int
    mixed_rank: int
    frequency_percentile: Decimal
    volume_percentile: Decimal
    mixed_score: Decimal


class ProductFlowAnalysisResponse(BaseModel):
    months: int = Field(ge=1, le=12)
    from_date: date
    to_date: date
    search: str | None = None
    sort_by: str
    order: str
    products_without_sales: int
    items: list[ProductFlowAnalysisItem]
    total: int
    skip: int
    limit: int


class ProductFlowSummary(BaseModel):
    months: int = Field(ge=1, le=12)
    from_date: date
    to_date: date
    products_without_sales: int
    top_products: list[ProductFlowItem]
    low_products: list[ProductFlowItem]


class MonthlySalesPoint(BaseModel):
    month: str
    sales_count: int
    units_sold: int
    total_amount: Decimal


class SystemSummaryResponse(BaseModel):
    days: int = Field(ge=1, le=365)
    cutoff_date: date
    generated_at: UTCDateTime

    catalogs: CatalogCounts
    invoices: InvoiceStatusCounts
    sales: SaleStatusCounts
    inventory: InventoryHealthCounts
    product_flow: ProductFlowSummary
    monthly_sales: list[MonthlySalesPoint]
