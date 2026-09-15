"""Persistence for orders. Internal to the orders module."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Numeric, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.types import OrderItem, OrderStatus


class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    items: Mapped[list[OrderItem]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default=OrderStatus.PENDING.value)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.utcnow())


async def create_order_row(session: AsyncSession, *, user_id: int,
                           items: list[OrderItem], total: Decimal) -> OrderRow:
    row = OrderRow(user_id=user_id, items=items, total=total)
    session.add(row)
    await session.flush()
    return row


async def list_orders_for_user(session: AsyncSession, *, user_id: int) -> list[OrderRow]:
    stmt = select(OrderRow).where(OrderRow.user_id == user_id).order_by(OrderRow.created_at.desc())
    return list((await session.execute(stmt)).scalars())
