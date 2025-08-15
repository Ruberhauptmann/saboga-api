import asyncio
import datetime
import time
from contextlib import asynccontextmanager

import docker
import pytest
from beanie import init_beanie
from faker import Faker
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi import create_app
from sabogaapi.models import Boardgame, RankHistory

fake = Faker()


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


@pytest.fixture(scope="session")
def docker_client():
    """Return a Docker client"""
    return docker.from_env()


@pytest.fixture
def mongodb_container(docker_client):
    container = docker_client.containers.run(
        "docker.io/mongo:8.0-noble",
        detach=True,
        name="pytest-mongodb",
        ports={"27017/tcp": 27017},
        environment={
            "MONGO_INITDB_ROOT_USERNAME": "mongoadmin",
            "MONGO_INITDB_ROOT_PASSWORD": "password",
            "MONGO_INITDB_DATABASE": "boardgames",
        },
    )
    yield container

    container.remove(force=True)


@pytest.fixture
def mongodb_host(mongodb_container):
    while True:
        mongodb_container.reload()
        try:
            networks = list(
                mongodb_container.attrs["NetworkSettings"]["Networks"].values()
            )
            addr = networks[0]["IPAddress"]
            return addr
        except KeyError:
            time.sleep(0.5)


@pytest.fixture
def small_dataset(mongodb_host):
    """Load a minimal deterministic dataset for quick tests"""
    uri = "mongodb://mongoadmin:password@127.0.0.1:27017/boardgames?authSource=admin"

    def _insert():
        async def _inner():
            client = AsyncIOMotorClient(uri)
            await init_beanie(
                database=client.get_database(), document_models=[Boardgame, RankHistory]
            )

            await Boardgame.delete_all()
            await RankHistory.delete_all()

            bg = Boardgame(name="Catan", bgg_id=1, bgg_rank=42)
            await bg.insert()
            rh = RankHistory(
                bgg_id=bg.bgg_id,
                bgg_rank=42,
                date=datetime.datetime.fromisoformat("2025-08-15"),
            )
            await rh.insert()
            return bg, rh

        return asyncio.run(_inner())

    return _insert


@pytest.fixture()
def app(mongodb_host):
    app = create_app(lifespan=lifespan)
    yield app
