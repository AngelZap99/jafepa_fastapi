from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, UniqueConstraint

from src.shared.models.base_model import MyBaseModel
from src.shared.enums.inventory_enums import (
    InventoryEventType,
    InventoryMovementType,
    InventorySourceType,
    InventoryValueType,
)


class InventoryMovement(MyBaseModel, table=True):
    __tablename__ = "inventory_movement"
    __table_args__ = (
        UniqueConstraint(
            "movement_group_id", "movement_sequence", name="uq_inv_mov_group_seq"
        ),
    )

    movement_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    movement_group_id: str = Field(
        default_factory=lambda: str(uuid4()), max_length=36, index=True
    )
    movement_sequence: int = Field(nullable=False)

    source_type: InventorySourceType = Field(nullable=False, index=True)
    event_type: InventoryEventType = Field(nullable=False, index=True)
    movement_type: InventoryMovementType = Field(nullable=False)
    value_type: InventoryValueType = Field(nullable=False, index=True)

    quantity: int = Field(nullable=False, gt=0)
    unit_cost: Decimal = Field(sa_type=Numeric(12, 6), nullable=False)
    prev_stock: int = Field(nullable=False)
    new_stock: int = Field(nullable=False)

    inventory_id: int = Field(foreign_key="inventory.id", nullable=False, index=True)
    invoice_line_id: Optional[int] = Field(
        default=None, foreign_key="invoice_line.id", index=True
    )
    sale_line_id: Optional[int] = Field(
        default=None, foreign_key="sale_line.id", index=True
    )

    inventory: Mapped[Optional["Inventory"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    invoice_line: Mapped[Optional["InvoiceLine"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    sale_line: Mapped[Optional["SaleLine"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
