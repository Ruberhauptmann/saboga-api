"""Database connection."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.models import Boardgame, Designer, RankHistory

from .config import settings


async def init_db() -> None:  # pragma: no cover
    client = AsyncIOMotorClient(  # type: ignore
        f"{settings.mongodb_uri}"
    )
    await init_beanie(
        database=client.get_database(),
        document_models=[Boardgame, RankHistory, Designer],
    )
