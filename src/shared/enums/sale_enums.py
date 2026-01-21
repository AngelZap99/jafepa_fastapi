from enum import Enum


class SaleStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"
