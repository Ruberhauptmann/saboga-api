from typing import AsyncGenerator

from beanie import init_beanie
from fastapi_users.db import BeanieUserDatabase
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.models import Boardgame, Collection, Play, User


async def get_user_db() -> AsyncGenerator[BeanieUserDatabase[User], None]:
    yield BeanieUserDatabase(User)


async def init_db() -> None:
    client = AsyncIOMotorClient("mongodb://saboga-database:27017/boardgames")
    await init_beanie(
        database=client.get_database(),
        document_models=[Boardgame, Play, User, Collection],
    )
