from __future__ import with_statement

import os
import sys

# Ensure root directory (the one containing `src/`) is on sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection

from alembic import context
from sabogaapi import models
from sabogaapi.database import sessionmanager

# Alembic Config object
config = context.config

# Setup loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate'
target_metadata = models.Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = str(sessionmanager.engine.url) if sessionmanager.engine else None
    if not url:
        raise RuntimeError("Engine not initialized in sessionmanager.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a live connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    if sessionmanager.engine is None:
        raise RuntimeError("Engine not initialized in sessionmanager.")

    async with sessionmanager.engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
