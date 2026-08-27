from collections.abc import AsyncIterator

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


class Base(DeclarativeBase):
    pass


try:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
except ModuleNotFoundError as exc:
    if exc.name == "asyncpg":
        raise ModuleNotFoundError(
            "asyncpg is missing from this Python. Use the project venv instead of Conda:\n"
            "  cd backend && .venv/bin/python -m uvicorn app.main:app --reload"
        ) from exc
    raise
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
