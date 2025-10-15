from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sabogaapi import schemas

TModel = TypeVar("TModel")
TSchema = TypeVar("TSchema")
TSchemaWithGames = TypeVar("TSchemaWithGames")
TNetworkModel = TypeVar("TNetworkModel")


class BaseEntityService(Generic[TModel, TSchema, TSchemaWithGames, TNetworkModel]):
    """Generic service for simple entities like Family, Category, Mechanic, Designer."""

    model: type[TModel]
    schema: type[TSchema]
    schema_with_games: type[TSchemaWithGames]
    network_model: type[TNetworkModel]

    @classmethod
    async def get_total_count(cls, db_session: AsyncSession) -> int:
        """Count all entities."""
        result = await db_session.execute(select(func.count()).select_from(cls.model))
        return result.scalar_one()

    @classmethod
    async def read_all(
        cls, db_session: AsyncSession, page: int = 1, per_page: int = 50
    ) -> list[TSchema]:
        """Paginated list of all entities ordered by name."""
        stmt = (
            select(cls.model)
            .order_by(cls.model.name.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await db_session.execute(stmt)
        items = result.scalars().all()
        return [cls.schema.model_validate(i) for i in items]

    @classmethod
    async def read_one(
        cls, db_session: AsyncSession, bgg_id: int
    ) -> TSchemaWithGames | None:
        """Fetch one entity by BGG ID including its boardgames."""
        stmt = (
            select(cls.model)
            .options(selectinload(cls.model.boardgames))
            .where(cls.model.bgg_id == bgg_id)
        )
        result = await db_session.execute(stmt)
        instance = result.scalars().first()
        if instance is None:
            return None
        return cls.schema_with_games.model_validate(instance)

    @classmethod
    async def get_network(cls, db_session: AsyncSession) -> schemas.Network:
        """Fetch the network representation."""
        stmt = select(cls.network_model).limit(1)
        result = await db_session.execute(stmt)
        network = result.scalars().first()
        if not network:
            return schemas.Network(nodes=[], edges=[])
        return schemas.Network.model_validate(network)
