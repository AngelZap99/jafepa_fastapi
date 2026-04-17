from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, DateTime, Numeric
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

from src.shared.models.base_model import MyBaseModel
from src.shared.enums.sale_enums import SaleStatus


class Sale(MyBaseModel, table=True):
    __tablename__ = "sale"

    sale_date: date = Field(default_factory=date.today, sa_type=Date, nullable=False)
    status: SaleStatus = Field(default=SaleStatus.DRAFT, nullable=False)

    total_price: Decimal = Field(
        default=Decimal("0.00"), sa_type=Numeric(12, 2), nullable=False
    )
    notes: Optional[str] = Field(default=None, max_length=500)

    client_id: int = Field(foreign_key="client.id", nullable=False, index=True)
    paid_by: Optional[int] = Field(default=None, nullable=True, foreign_key="users.id")
    cancelled_by: Optional[int] = Field(
        default=None, nullable=True, foreign_key="users.id"
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )
    cancelled_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )

    client: Mapped[Optional["Client"]] = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )

    lines: Mapped[List["SaleLine"]] = Relationship(
        back_populates="sale",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin",
            "order_by": "SaleLine.id",
        },
    )
