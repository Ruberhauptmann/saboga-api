import pytest
from fastapi.testclient import TestClient

from sabogaapi import create_app


@pytest.fixture(name="client")
def client_fixture():
    app = create_app()
    client = TestClient(app)
    yield client
