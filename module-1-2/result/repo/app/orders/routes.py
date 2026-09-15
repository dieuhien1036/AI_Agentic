"""Order endpoints. The reference pattern for any new endpoint:

  1. Define request/response models in app/types.py.
  2. Add the route here.
  3. Add an integration test under tests/integration/test_orders.py.
  4. No business logic in route handlers — delegate to a function in this
     module or a sibling.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.orders.repository import OrderRow, create_order_row, list_orders_for_user
from app.types import CreateOrderRequest, Order, OrderStatus

router = APIRouter()


def _row_to_order(row: OrderRow) -> Order:
    return Order(
        id=row.id,
        user_id=row.user_id,
        items=row.items,
        status=OrderStatus(row.status),
        total=row.total,
        created_at=row.created_at,
    )


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(req: CreateOrderRequest,
                       session: AsyncSession = Depends(get_session)) -> Order:
    if not req.items:
        raise HTTPException(status_code=400, detail="items required")
    total: Decimal = sum((it.unit_price * it.quantity for it in req.items), start=Decimal("0"))
    row = await create_order_row(session, user_id=req.user_id, items=req.items, total=total)
    await session.commit()
    return _row_to_order(row)


@router.get("", response_model=list[Order])
async def list_orders(user_id: int,
                      session: AsyncSession = Depends(get_session)) -> list[Order]:
    rows = await list_orders_for_user(session, user_id=user_id)
    return [_row_to_order(r) for r in rows]
