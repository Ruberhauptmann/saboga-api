"""Database connection."""

import contextlib
from collections.abc import AsyncGenerator, AsyncIterator
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine

from sqlalchemy.orm import declarative_base

from .config import settings

Base = declarative_base()


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None) -> None:
        if engine_kwargs is None:
            engine_kwargs = {}
        self.engine: AsyncEngine | None = create_async_engine(host, **engine_kwargs)
        self.sessionmaker: async_sessionmaker | None = async_sessionmaker(
            autocommit=False, bind=self.engine
        )

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


_sessionmanager: DatabaseSessionManager | None = None


def _ensure_sessionmanager() -> DatabaseSessionManager:
    """Create the DatabaseSessionManager lazily when the settings are available."""
    global _sessionmanager
    # If there is no session manager, or the existing one was closed (engine/sessionmaker None),
    # create a fresh DatabaseSessionManager. This handles the case where the manager
    # was previously closed (for example during an app lifespan shutdown) and
    # tests need to recreate it.
    if (
        _sessionmanager is None
        or getattr(_sessionmanager, "engine", None) is None
        or getattr(_sessionmanager, "sessionmaker", None) is None
    ):
        if not settings.postgres_uri:
            msg = "DatabaseSessionManager is not initialized: settings.postgres_uri not set"
            raise RuntimeError(msg)
        _sessionmanager = DatabaseSessionManager(
            str(settings.postgres_uri), {"echo": settings.echo_sql}
        )
    return _sessionmanager


class _SessionManagerProxy:
    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        async with _ensure_sessionmanager().connect() as connection:
            yield connection

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with _ensure_sessionmanager().session() as session:
            yield session

    async def close(self) -> None:
        await _ensure_sessionmanager().close()

    @property
    def engine(self):
        # Return the underlying engine if already created, otherwise None.
        return _sessionmanager.engine if _sessionmanager is not None else None


# Export a proxy so modules can import `sessionmanager` at import-time
# but actual engine/sessionmaker creation is deferred until first use.
sessionmanager: _SessionManagerProxy = _SessionManagerProxy()


async def get_db_session() -> AsyncGenerator:
    async with sessionmanager.session() as session:
        yield session
