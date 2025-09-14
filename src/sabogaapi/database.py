"""Database connection."""

from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi import models

from .config import settings


async def init_db() -> None:  # pragma: no cover
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(
        f"{settings.mongodb_uri}",
    )
    await init_beanie(
        database=client.get_database(),
        document_models=[
            models.Boardgame,
            models.BoardgameNetwork,
            models.RankHistory,
            models.Category,
            models.CategoryNetwork,
            models.Designer,
            models.DesignerNetwork,
            models.Family,
            models.FamilyNetwork,
            models.Mechanic,
            models.MechanicNetwork,
        ],
    )
