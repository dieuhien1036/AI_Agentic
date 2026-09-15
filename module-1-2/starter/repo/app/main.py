from __future__ import annotations

from fastapi import FastAPI

from app.auth.handlers import router as auth_router
from app.orders.routes import router as orders_router

app = FastAPI(title="payments-api", version="0.3.1")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
