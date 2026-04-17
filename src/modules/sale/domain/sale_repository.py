from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.shared.models.sale.sale_model import Sale
from src.shared.models.sale_line.sale_line_model import SaleLine
from src.shared.models.inventory.inventory_model import Inventory
from src.shared.models.client.client_model import Client


class SaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self, skip: int = 0, limit: Optional[int] = None, include_inactive: bool = True
    ) -> List[Sale]:
        q = (
            select(Sale)
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
            q = q.where(Sale.is_active == True)  # noqa: E712

        q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return self.db.execute(q).scalars().all()

    def get(self, sale_id: int, include_inactive: bool = False) -> Optional[Sale]:
        q = (
            select(Sale)
            .options(
                selectinload(Sale.lines).selectinload(SaleLine.inventory),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.product),
                selectinload(Sale.lines)
                .selectinload(SaleLine.inventory)
                .selectinload(Inventory.warehouse),
            )
            .where(Sale.id == sale_id)
        )

        if not include_inactive:
            q = q.where(Sale.is_active == True)  # noqa: E712

        return self.db.execute(q).scalars().first()

    def add(self, sale: Sale, commit: bool = True) -> Sale:
        self.db.add(sale)
        if commit:
            self.db.commit()
            self.db.refresh(sale)
        return sale

    def update(self, sale: Sale, commit: bool = True) -> Sale:
        self.db.add(sale)
        if commit:
            self.db.commit()
            self.db.refresh(sale)
        return sale

    def soft_delete(self, sale: Sale, commit: bool = True) -> Sale:
        sale.is_active = False
        for line in sale.lines:
            line.is_active = False
        self.db.add(sale)
        if commit:
            self.db.commit()
            self.db.refresh(sale)
        return sale

    def add_line(self, sale: Sale, line: SaleLine, commit: bool = True) -> SaleLine:
        line.sale_id = sale.id
        if line not in sale.lines:
            sale.lines.append(line)
        self.db.add(line)
        if commit:
            self.db.commit()
            self.db.refresh(line)
        else:
            self.db.flush()
            self.db.refresh(line)
        return line

    def get_line(
        self, sale_id: int, line_id: int, include_inactive: bool = False
    ) -> Optional[SaleLine]:
        q = (
            select(SaleLine)
            .options(
                selectinload(SaleLine.inventory),
                selectinload(SaleLine.inventory).selectinload(Inventory.product),
                selectinload(SaleLine.inventory).selectinload(Inventory.warehouse),
            )
            .where(SaleLine.id == line_id, SaleLine.sale_id == sale_id)
        )

        if not include_inactive:
            q = q.where(SaleLine.is_active == True)  # noqa: E712

        return self.db.execute(q).scalars().first()

    def update_line(self, line: SaleLine, commit: bool = True) -> SaleLine:
        self.db.add(line)
        if commit:
            self.db.commit()
            self.db.refresh(line)
        else:
            self.db.flush()
            self.db.refresh(line)
        return line

    def soft_delete_line(self, line: SaleLine, commit: bool = True) -> SaleLine:
        line.is_active = False
        self.db.add(line)
        if commit:
            self.db.commit()
            self.db.refresh(line)
        else:
            self.db.flush()
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
            select(SaleLine)
            .join(SaleLine.sale)
            .options(
                selectinload(SaleLine.inventory),
                selectinload(SaleLine.inventory).selectinload(Inventory.product),
                selectinload(SaleLine.inventory).selectinload(Inventory.warehouse),
                selectinload(SaleLine.sale).selectinload(Sale.client),
            )
            .where(
                Sale.is_active == True,  # noqa: E712
                SaleLine.is_active == True,  # noqa: E712
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date,
            )
        )

        if status is not None:
            q = q.where(Sale.status == status)
        if client_id is not None:
            q = q.where(Sale.client_id == client_id)
        if inventory_id is not None:
            q = q.where(SaleLine.inventory_id == inventory_id)

        if product_id is not None or warehouse_id is not None:
            q = q.join(Inventory)
            if product_id is not None:
                q = q.where(Inventory.product_id == product_id)
            if warehouse_id is not None:
                q = q.where(Inventory.warehouse_id == warehouse_id)

        return self.db.execute(q.order_by(Sale.id, SaleLine.id)).scalars().all()
