from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.client.client_model import Client


class SaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> List[Sale]:
        q = (
            self.db.query(Sale)
            .options(
                selectinload(Sale.lines).selectinload(SaleLine.inventory),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.product),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.warehouse),
            )
            .order_by(Sale.id)
        )

        if not include_inactive:
            q = q.filter(Sale.is_active == True)  # noqa: E712

        return q.offset(skip).limit(limit).all()

    def get(self, sale_id: int, include_inactive: bool = False) -> Optional[Sale]:
        q = (
            self.db.query(Sale)
            .options(
                selectinload(Sale.lines).selectinload(SaleLine.inventory),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.product),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.warehouse),
            )
            .filter(Sale.id == sale_id)
        )

        if not include_inactive:
            q = q.filter(Sale.is_active == True)  # noqa: E712

        return q.first()

    def add(self, sale: Sale) -> Sale:
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def update(self, sale: Sale) -> Sale:
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def soft_delete(self, sale: Sale) -> Sale:
        sale.is_active = False
        for line in sale.lines:
            line.is_active = False
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def add_line(self, sale: Sale, line: SaleLine) -> SaleLine:
        line.sale_id = sale.id
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def get_line(
        self, sale_id: int, line_id: int, include_inactive: bool = False
    ) -> Optional[SaleLine]:
        q = (
            self.db.query(SaleLine)
            .options(selectinload(SaleLine.inventory))
            .filter(SaleLine.id == line_id, SaleLine.sale_id == sale_id)
        )

        if not include_inactive:
            q = q.filter(SaleLine.is_active == True)  # noqa: E712

        return q.first()

    def update_line(self, line: SaleLine) -> SaleLine:
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def soft_delete_line(self, line: SaleLine) -> SaleLine:
        line.is_active = False
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def list_lines_for_report(
        self,
        from_date,
        to_date,
        status=None,
        client_id=None,
        product_id=None,
        warehouse_id=None,
        inventory_id=None,
    ):
        q = (
            self.db.query(SaleLine)
            .join(SaleLine.sale)
            .options(
                selectinload(SaleLine.inventory),
                selectinload(SaleLine.inventory).selectinload(Inventory.product),
                selectinload(SaleLine.inventory).selectinload(Inventory.warehouse),
                selectinload(SaleLine.sale).selectinload(Sale.client),
            )
            .filter(
                Sale.is_active == True,  # noqa: E712
                SaleLine.is_active == True,  # noqa: E712
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date,
            )
        )

        if status is not None:
            q = q.filter(Sale.status == status)
        if client_id is not None:
            q = q.filter(Sale.client_id == client_id)
        if inventory_id is not None:
            q = q.filter(SaleLine.inventory_id == inventory_id)

        if product_id is not None or warehouse_id is not None:
            q = q.join(Inventory)
            if product_id is not None:
                q = q.filter(Inventory.product_id == product_id)
            if warehouse_id is not None:
                q = q.filter(Inventory.warehouse_id == warehouse_id)

        return q.order_by(Sale.id, SaleLine.id).all()
