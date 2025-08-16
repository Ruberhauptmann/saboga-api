from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi.models import Boardgame, RankHistory


def test_rank_history_small(
    app: FastAPI, small_dataset: Callable[[], tuple[Boardgame, RankHistory]]
):
    bg, rh = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history")

    assert response.status_code == 200
    data = response.json()
    assert any(item["bgg_id"] == bg.bgg_id for item in data)


def test_trending_small(
    app: FastAPI, small_dataset: Callable[[], tuple[Boardgame, RankHistory]]
):
    bg, rh = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/trending")

    assert response.status_code == 200


def test_declining_small(
    app: FastAPI, small_dataset: Callable[[], tuple[Boardgame, RankHistory]]
):
    bg, rh = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/declining")

    assert response.status_code == 200
