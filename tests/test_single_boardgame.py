from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabogaapi.models import Boardgame, RankHistory


def test_single_boardgame_small(
    app: FastAPI, small_dataset: Callable[[], tuple[Boardgame, RankHistory]]
):
    bg, rh = small_dataset()

    with TestClient(app) as client:
        response = client.get(f"/boardgames/{bg.bgg_id}")

    assert response.status_code == 200
