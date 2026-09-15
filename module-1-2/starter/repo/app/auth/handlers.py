"""Authentication endpoints.

SECURITY-SENSITIVE. Any change here must go through human review with the
security lead before merge. Do not modify token TTLs, signing keys, or
password verification without explicit approval.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.types import LoginRequest, TokenResponse

router = APIRouter()

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_JWT_SECRET = os.environ["JWT_SECRET"]
_JWT_ALG = "HS256"
_TOKEN_TTL = timedelta(hours=24)


def _make_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": int(now.timestamp()),
               "exp": int((now + _TOKEN_TTL).timestamp())}
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALG)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    # Lookup user by email; constant-time compare on password hash.
    from app.auth.queries import get_user_by_email  # local import to avoid cycles
    user = await get_user_by_email(session, req.email)
    if not user or not _pwd.verify(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return TokenResponse(access_token=_make_token(user.id), expires_in=int(_TOKEN_TTL.total_seconds()))
