import asyncio
import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Generator

import pytest
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory
from sabogaapi.main import create_app


async def init_db_mock():
    Path("static").mkdir(exist_ok=True, parents=True)
    client = AsyncMongoMockClient()
    await init_beanie(
        document_models=[Boardgame, RankHistory],
        database=client.get_database(name="boardgames"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_mock()
    yield


@pytest.fixture()
def app():
    app = create_app(lifespan=lifespan)
    yield app


@pytest.fixture()
def client(app) -> Generator:
    yield TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


async def setup_database():
    await init_db()


async def seed_test_data():
    await Boardgame.delete_all()
    await RankHistory.delete_all()

    boardgames = [
        Boardgame(
            bgg_id=i,
            name=f"Game {i}",
            bgg_rank=i,
            bgg_average_rating=7.0 + (i % 2),
            bgg_geek_rating=6.0 + (i % 2),
        )
        for i in range(100)
    ]
    await Boardgame.insert_many(boardgames)

    rank_history = [
        RankHistory(
            bgg_id=i,
            date=datetime.datetime.now() - datetime.timedelta(days=30),
            bgg_rank=i + 1,
            bgg_average_rating=6.5 + (i % 2),
            bgg_geek_rating=5.5 + (i % 2),
        )
        for i in range(100)
    ]
    await RankHistory.insert_many(rank_history)
