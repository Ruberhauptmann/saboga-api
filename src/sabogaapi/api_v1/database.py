from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.models import Boardgame, Play


async def init_db():
    client = AsyncIOMotorClient("mongodb://saboga-database:27017/boardgames")
    await init_beanie(database=client.get_database(), document_models=[Boardgame, Play])
