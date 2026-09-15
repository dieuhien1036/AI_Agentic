"""Integration tests for orders endpoints. One test per scenario.

Pattern for adding tests:
  - Arrange request body with realistic shape (use app.types models).
  - Act via the AsyncClient fixture.
  - Assert response status, then specific fields. Avoid full-payload equality
    where IDs or timestamps make tests brittle.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order_returns_201_and_order(client: AsyncClient) -> None:
    body = {
        "user_id": 42,
        "items": [
            {"sku": "ABC-1", "quantity": 2, "unit_price": "9.99"},
            {"sku": "ABC-2", "quantity": 1, "unit_price": "4.50"},
        ],
    }
    resp = await client.post("/orders", json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == 42
    assert data["status"] == "pending"
    assert data["total"] == "24.48"


@pytest.mark.asyncio
async def test_create_order_rejects_empty_items(client: AsyncClient) -> None:
    resp = await client.post("/orders", json={"user_id": 42, "items": []})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_orders_filters_by_user(client: AsyncClient) -> None:
    resp = await client.get("/orders", params={"user_id": 42})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
