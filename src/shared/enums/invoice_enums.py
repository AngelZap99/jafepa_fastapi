from enum import Enum


class InvoiceStatus(str, Enum):
    # Keep statuses explicit to avoid magic strings across the codebase
    DRAFT = "DRAFT"
    ARRIVED = "ARRIVED"
    CANCELLED = "CANCELLED"


class InvoiceLinePriceType(str, Enum):
    UNIT = "UNIT"
    BOX = "BOX"
