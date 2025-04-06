from contextlib import asynccontextmanager
from pathlib import Path
from typing import Generator

import pytest
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

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
