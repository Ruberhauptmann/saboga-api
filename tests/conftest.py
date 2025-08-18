import asyncio
import datetime
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

import docker
import pytest
from beanie import init_beanie
from docker.models.containers import Container
from faker import Faker
from fastapi import FastAPI
from pydantic import MongoDsn

from sabogaapi import create_app, models
from sabogaapi.config import settings
from sabogaapi.database import init_db
from sabogaapi.main import lifespan
from sabogaapi.scraper._fill_in_data import construct_designer_network

fake = Faker()


@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Return a Docker client"""
    return docker.from_env()


@pytest.fixture(scope="session")
def mongodb_container(docker_client: docker.DockerClient):
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


@pytest.fixture(scope="session")
def mongodb_host(mongodb_container: Container) -> str:
    while True:
        mongodb_container.reload()
        try:
            networks = list(
                mongodb_container.attrs["NetworkSettings"]["Networks"].values(),
            )
            return networks[0]["IPAddress"]
        except KeyError:
            time.sleep(0.5)


@pytest.fixture(scope="function")
def small_dataset(
    mongodb_host: str,
):
    """Load a minimal deterministic dataset for quick tests"""

    def _insert():
        async def _inner():
            settings.mongodb_uri = MongoDsn(
                "mongodb://mongoadmin:password@127.0.0.1/boardgames?authSource=admin"
            )
            await init_db()

            await models.Boardgame.delete_all()
            await models.RankHistory.delete_all()
            await models.Designer.delete_all()

            de = [
                models.Designer(name="Vlaada Chvátil", bgg_id=1),
                models.Designer(name="Klaus Teuber", bgg_id=2),
            ]
            insert_result = await models.Designer.insert_many(de)
            de = [await models.Designer.get(_id) for _id in insert_result.inserted_ids]

            bg = [
                models.Boardgame(
                    name="Through the Ages: A New Story of Civilization",
                    bgg_id=1,
                    bgg_rank=1,
                    bgg_geek_rating=8.5,
                    bgg_average_rating=8.4,
                    designers=[de[0]],
                ),
                models.Boardgame(
                    name="Catan",
                    bgg_id=2,
                    bgg_rank=2,
                    bgg_geek_rating=7.5,
                    bgg_average_rating=7.6,
                    designers=[de[1]],
                ),
                models.Boardgame(
                    name="Yet undisclosed Teuber-Chvátil game",
                    bgg_id=3,
                    bgg_rank=3,
                    bgg_geek_rating=6.5,
                    bgg_average_rating=6.7,
                    designers=de,
                ),
            ]
            await models.Boardgame.insert_many(bg)
            rh = [
                models.RankHistory(
                    bgg_id=bg[0].bgg_id,
                    bgg_rank=2,
                    bgg_geek_rating=7.8,
                    bgg_average_rating=7.9,
                    date=datetime.datetime.now() - datetime.timedelta(days=7),
                ),
                models.RankHistory(
                    bgg_id=bg[1].bgg_id,
                    bgg_rank=1,
                    bgg_geek_rating=8.1,
                    bgg_average_rating=8.2,
                    date=datetime.datetime.now() - datetime.timedelta(days=7),
                ),
                models.RankHistory(
                    bgg_id=bg[2].bgg_id,
                    bgg_rank=3,
                    bgg_geek_rating=7.0,
                    bgg_average_rating=7.1,
                    date=datetime.datetime.now() - datetime.timedelta(days=7),
                ),
            ]
            await models.RankHistory.insert_many(rh)
            nodes, edges = await construct_designer_network()
            await models.DesignerNetwork.delete_all()
            new_graph = models.DesignerNetwork(
                nodes=nodes,
                edges=edges,
            )
            await new_graph.insert()

            return bg, rh, de

        return asyncio.run(_inner())

    return _insert


@pytest.fixture(scope="session")
def app(mongodb_host: str) -> FastAPI:
    settings.mongodb_uri = MongoDsn(
        "mongodb://mongoadmin:password@127.0.0.1/boardgames?authSource=admin"
    )
    app = create_app(lifespan=lifespan)
    return app
