from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_single_boardgame_small(app: FastAPI, small_dataset):
    bg, rh, de = small_dataset()

    for bg_single in bg:
        with TestClient(app) as client:
            response = client.get(f"/boardgames/{bg_single.bgg_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == bg_single.name
        assert data["bgg_rank"] == bg_single.bgg_rank
