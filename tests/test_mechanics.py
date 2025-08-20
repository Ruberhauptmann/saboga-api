from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi.models import Boardgame, Designer, RankHistory


def test_all_mechanics(app: FastAPI, small_dataset):
    data = small_dataset()
    me_ids = [item.bgg_id for item in data["mechanics"]]

    with TestClient(app) as client:
        response = client.get("/mechanics/")

    assert response.status_code == 200
    api_data = list(response.json())
    assert len(api_data) == len(data["mechanics"])
    assert all([item["bgg_id"] in me_ids for item in api_data])


def test_single_mechanic(app: FastAPI, small_dataset):
    data = small_dataset()
    de_ids = [item.bgg_id for item in data["mechanics"]]

    for i, bgg_id in enumerate(de_ids):
        with TestClient(app) as client:
            response = client.get(f"/mechanics/{bgg_id}")

        assert response.status_code == 200
        api_data = response.json()
        assert data["mechanics"][i].name == api_data["name"]

def test_nonexisting_mechanic(app: FastAPI, small_dataset):
    _ = small_dataset()
    with TestClient(app) as client:
        response = client.get(f"/mechanics/1000")

    assert response.status_code == 404
