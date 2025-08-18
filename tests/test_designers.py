from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi.models import Boardgame, Designer, RankHistory


def test_all_designers_small(app: FastAPI, small_dataset):
    bg, rh, de = small_dataset()
    de_ids = [item.bgg_id for item in de]

    with TestClient(app) as client:
        response = client.get("/designers/")

    assert response.status_code == 200
    data = list(response.json())
    assert len(data) == 2
    assert all([item["bgg_id"] in de_ids for item in data])


def test_designer_network_small(app: FastAPI, small_dataset):
    bg, rh, de = small_dataset()
    de_ids = [item.bgg_id for item in de]

    with TestClient(app) as client:
        response = client.get("/designers/clusters")

    assert response.status_code == 200
    data = dict(response.json())
    print(data, flush=True)
    assert len(data["nodes"]) == len(de)
    assert len(data["edges"]) == 1
    assert int(data["edges"][0]["source"]) == 1
    assert int(data["edges"][0]["target"]) == 2
