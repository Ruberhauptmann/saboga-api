"""Database connection."""

import contextlib
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import declarative_base

from .config import settings

Base = declarative_base()


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None) -> None:
        if engine_kwargs is None:
            engine_kwargs = {}
        self.engine: AsyncEngine | None = create_async_engine(host, **engine_kwargs)
        self.sessionmaker = async_sessionmaker(autocommit=False, bind=self.engine)

    async def close(self) -> None:
        if self.engine is None:
            msg = "DatabaseSessionManager is not initialized"
            raise RuntimeError(msg)
        await self.engine.dispose()

        self.engine = None
        self.sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self.engine is None:
            msg = "DatabaseSessionManager is not initialized"
            raise RuntimeError(msg)

        async with self.engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.sessionmaker is None:
            msg = "DatabaseSessionManager is not initialized"
            raise RuntimeError(msg)

        session = self.sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(
    str(settings.postgres_uri), {"echo": settings.echo_sql}
)


async def get_db_session() -> AsyncSession:
    async with sessionmanager.session() as session:
        yield session
