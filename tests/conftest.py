import time
from contextlib import asynccontextmanager

import docker
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


@pytest.fixture()
def app(mongodb_host):
    app = create_app(lifespan=lifespan)
    yield app
