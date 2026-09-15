"""Test fixtures.

Integration tests run against a real Postgres started by testcontainers.
Do not switch to SQLite — the app uses Postgres-only features. If you need a
faster test mode, use the unit suite (tests/unit/).
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
