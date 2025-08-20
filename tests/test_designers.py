from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi.models import Boardgame, Designer, RankHistory


def test_all_designers(app: FastAPI, small_dataset):
    data = small_dataset()
    de_ids = [item.bgg_id for item in data["designers"]]

    with TestClient(app) as client:
        response = client.get("/designers/")

    assert response.status_code == 200
    api_data = list(response.json())
    assert len(api_data) == len(data["designers"])
    assert all([item["bgg_id"] in de_ids for item in api_data])


def test_single_designer(app: FastAPI, small_dataset):
    data = small_dataset()
    de_ids = [item.bgg_id for item in data["designers"]]

    for i, bgg_id in enumerate(de_ids):
        with TestClient(app) as client:
            response = client.get(f"/designers/{bgg_id}")

        assert response.status_code == 200
        api_data = response.json()
        assert data["designers"][i].name == api_data["name"]


def test_designer_network(app: FastAPI, small_dataset):
    data = small_dataset()

    with TestClient(app) as client:
        response = client.get("/designers/clusters")

    assert response.status_code == 200
    api_data = dict(response.json())
    assert len(api_data["nodes"]) == len(data["designers"])
    assert len(api_data["edges"]) == 1
    assert int(api_data["edges"][0]["source"]) == 1
    assert int(api_data["edges"][0]["target"]) == 2
