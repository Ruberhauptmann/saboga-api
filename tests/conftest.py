from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


@pytest.fixture(name="client")
def client_fixture():
    app = create_app(lifespan=lifespan)
    client = TestClient(app)
    yield client
