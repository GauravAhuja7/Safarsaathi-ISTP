import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url

    # SQLite — no server needed, file stored next to this repo
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False, connect_args={"check_same_thread": False})

    # PostgreSQL (when available)
    return create_async_engine(url, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=10)


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
