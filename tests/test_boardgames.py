import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_rank_history_small(app: FastAPI, small_dataset):
    data = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history")

    assert response.status_code == 200
    data_api = list(response.json())

    assert len(data_api) == len(data["boardgames"])

    for i, game in enumerate(data["boardgames"]):
        history_entry = data["rank_histories"][i]
        game_api = data_api[i]

        assert game.bgg_rank == game_api["bgg_rank"]
        assert pytest.approx(game_api["bgg_rank_change"]) == -(
            game.bgg_rank - history_entry.bgg_rank
        )
        assert (
            pytest.approx(game_api["bgg_geek_rating_change"])
            == game.bgg_geek_rating - history_entry.bgg_geek_rating
        )
        assert (
            pytest.approx(game_api["bgg_average_rating_change"])
            == game.bgg_average_rating - history_entry.bgg_average_rating
        )
