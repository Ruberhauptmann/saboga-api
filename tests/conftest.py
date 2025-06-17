from contextlib import asynccontextmanager

import pytest
from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.models import Boardgame, RankHistory
from sabogaapi.main import create_app


async def init_db():
    client = AsyncIOMotorClient(
        "mongodb://api-user:password@127.0.0.1/boardgames?authSource=boardgames"
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
