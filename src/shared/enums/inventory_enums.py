from enum import Enum


class InventorySourceType(str, Enum):
    INVOICE = "INVOICE"
    SALE = "SALE"
    MANUAL = "MANUAL"


class InventoryEventType(str, Enum):
    INVOICE_RECEIVED = "INVOICE_RECEIVED"
    INVOICE_UNRECEIVED = "INVOICE_UNRECEIVED"
    SALE_RESERVED = "SALE_RESERVED"
    SALE_RELEASED = "SALE_RELEASED"
    SALE_APPROVED = "SALE_APPROVED"
    SALE_REVERSED = "SALE_REVERSED"
    BOX_OPENED_OUT = "BOX_OPENED_OUT"
    BOX_OPENED_IN = "BOX_OPENED_IN"
    MANUAL_CREATED = "MANUAL_CREATED"
    MANUAL_STOCK_ADJUSTED = "MANUAL_STOCK_ADJUSTED"
    # TODO: Add other type events: SALE_APPROVED, SALE_REJECTED, etc.


class InventoryMovementType(str, Enum):
    IN_ = "IN"  # Stock increases
    OUT = "OUT"  # Stock decreases


class InventoryValueType(str, Enum):
    COST = "COST"
    PRICE = "PRICE"
