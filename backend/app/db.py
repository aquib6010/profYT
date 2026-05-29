"""Async SQLAlchemy engine, declarative base, and session factory.

Supports both SQLite (dev) and Postgres (Supabase / production) via DATABASE_URL.
For Supabase's transaction pooler, asyncpg's prepared-statement cache MUST be
disabled — the pooler rotates server-side connections per transaction, so
prepared statements made on one connection won't exist on the next.

Disabling the caches is necessary but NOT sufficient: SQLAlchemy's asyncpg
dialect still issues named prepared statements (e.g. for dialect introspection),
and asyncpg names them deterministically (`__asyncpg_stmt_4__`). Under the
transaction pooler, two requests can land on different physical backends, so a
name created on one backend collides with a leftover of the same name on
another -> `DuplicatePreparedStatementError`. Giving every prepared statement a
unique name (prepared_statement_name_func) makes collisions impossible.
"""

import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

_connect_args: dict[str, object] = (
    {}
    if _is_sqlite
    else {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        # Unique name per statement so pooled backends never collide.
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    }
)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Parent class for every ORM model. Imported by app.models.*"""


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a transactional session."""
    async with AsyncSessionLocal() as session:
        yield session
