from contextlib import asynccontextmanager

import pytest
from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi import create_app
from sabogaapi.models import Boardgame, RankHistory


async def init_db():
    client = AsyncIOMotorClient(
        "mongodb://mongoadmin:password@127.0.0.1/boardgames?authSource=admin"
    )
    await init_beanie(
        document_models=[Boardgame, RankHistory],
        database=client.get_database(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


@pytest.fixture()
def app():
    app = create_app(lifespan=lifespan)
    yield app
