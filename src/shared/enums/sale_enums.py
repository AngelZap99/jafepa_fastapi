from enum import Enum


class SaleStatus(str, Enum):
    DRAFT = "DRAFT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

    @classmethod
    def _missing_(cls, value):  # type: ignore[override]
        # Backward compatibility: legacy status stored as "APPROVED" should behave as PAID.
        if isinstance(value, str) and value.upper() == "APPROVED":
            return cls.PAID
        return None


class SaleLinePriceType(str, Enum):
    UNIT = "UNIT"
    BOX = "BOX"


class SaleLineQuantityMode(str, Enum):
    BOX = "BOX"
    UNIT = "UNIT"
