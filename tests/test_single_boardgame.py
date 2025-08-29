from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_single_boardgame(app: FastAPI, small_dataset):
    data = small_dataset()

    for bg_single in data["boardgames"]:
        with TestClient(app) as client:
            response = client.get(f"/boardgames/{bg_single.bgg_id}")

        assert response.status_code == 200
        api_data = response.json()
        assert api_data["name"] == bg_single.name
        assert api_data["bgg_rank"] == bg_single.bgg_rank


def test_nonexisting_boardgame(app: FastAPI, small_dataset):
    _ = small_dataset()
    with TestClient(app) as client:
        response = client.get(f"/boardgames/1000")

    assert response.status_code == 404
