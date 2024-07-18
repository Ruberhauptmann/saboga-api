import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.models import Boardgame, BoardgameSettings


async def init_db() -> None:
    db_password = os.getenv("MONGODB_API_USER")
    client = AsyncIOMotorClient(  # type: ignore
        f"mongodb://api-user:{db_password}@saboga-database:27017/"
        "boardgames?authSource=boardgames"
    )
    await init_beanie(
        database=client.get_database(),
        document_models=[Boardgame, BoardgameSettings],
    )
