"""Auth-related database queries. Internal — not exported."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]


async def get_user_by_email(session: AsyncSession, email: str) -> UserRow | None:
    stmt = select(UserRow).where(UserRow.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()
