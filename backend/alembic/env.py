"""Alembic environment — async, reads DATABASE_URL from app.config.

We override `sqlalchemy.url` programmatically rather than relying on alembic.ini
so the connection string lives in exactly one place (.env). Supabase's
transaction pooler requires disabling asyncpg's prepared-statement cache.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Make `app.*` importable when alembic is run from the backend/ directory.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402
from app.models import Creator, DailyAnalytics, Video  # noqa: E402,F401  (register models)

# Alembic Config object.
config = context.config

# Logging config from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the real DATABASE_URL from our settings into Alembic's config.
# Configparser uses `%` for interpolation, so we escape any literal `%` to `%%`.
# This matters because URL-encoded passwords (e.g. "%40" for "@") would otherwise
# raise InterpolationSyntaxError.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

# Metadata for autogenerate.
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    """Restrict Alembic to *our* tables only.

    The Supabase project may host tables belonging to other apps (e.g. the
    pre-existing ApplyRadar schema). Without this filter, autogenerate would
    emit DROP TABLE for anything not in our metadata. We exclude any object
    whose owning table isn't in our metadata.
    """
    if type_ == "table":
        return name in target_metadata.tables
    parent_table = getattr(object, "table", None)
    if parent_table is not None:
        return parent_table.name in target_metadata.tables
    return True

# Pooler-safe connect args for asyncpg + Supabase (no effect on SQLite).
_is_sqlite = settings.database_url.startswith("sqlite")
_connect_args: dict[str, object] = (
    {} if _is_sqlite else {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
)


def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
