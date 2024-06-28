import os
from typing import AsyncGenerator

from beanie import init_beanie
from fastapi_users.db import BeanieUserDatabase
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.models import Boardgame, Collection, Play, User


async def get_user_db() -> AsyncGenerator[BeanieUserDatabase[User], None]:
    yield BeanieUserDatabase(User)


async def init_db() -> None:
    db_password = os.getenv("MONGODB_API_USER")
    client = AsyncIOMotorClient(
        f"mongodb://api-user:{db_password}@saboga-database:27017/"
        "boardgames?authSource=boardgames"
    )
    await init_beanie(
        database=client.get_database(),
        document_models=[Boardgame, Play, User, Collection],
    )
