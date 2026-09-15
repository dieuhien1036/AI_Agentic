"""Public types shared across modules.

Anything that crosses a module boundary lives here. Internal types stay in
their respective modules.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)


class Order(BaseModel):
    id: int
    user_id: int
    items: list[OrderItem]
    status: OrderStatus
    total: Decimal
    created_at: datetime


class CreateOrderRequest(BaseModel):
    user_id: int
    items: list[OrderItem]


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
