from __future__ import annotations

from datetime import date

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


class SaleStatusCounts(BaseModel):
    pending: int
    cancelled: int
    paid_last_n_days: int


class SystemSummaryResponse(BaseModel):
    days: int = Field(ge=1, le=365)
    cutoff_date: date
    generated_at: UTCDateTime

    catalogs: CatalogCounts
    invoices: InvoiceStatusCounts
    sales: SaleStatusCounts
