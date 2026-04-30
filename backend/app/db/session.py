import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url

    # SQLite: NullPool avoids stale WAL read-snapshot bugs when connections are reused.
    # Each request gets a fresh connection with an up-to-date view of the database.
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False, poolclass=NullPool, connect_args={"check_same_thread": False})

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
