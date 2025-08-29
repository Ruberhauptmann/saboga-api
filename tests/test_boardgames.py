import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_read_all_games(app: FastAPI):
    with TestClient(app) as client:
        response = client.get("/boardgames")
    assert response.json() == {"status": "not yet implemented"}


def test_read_games_with_volatility(app: FastAPI):
    with TestClient(app) as client:
        response = client.get("/boardgames/volatile")
    assert response.json() == {"status": "not yet implemented"}


def test_read_trending_games(app: FastAPI, small_dataset):
    data = small_dataset()

    with TestClient(app) as client:
        response = client.get("boardgames/trending")

    data = response.json()

    assert data[0]["bgg_id"] == 1
    assert data[0]["bgg_rank_trend"] == 66.66666666666666

    assert data[2]["bgg_id"] == 2
    assert data[2]["bgg_rank_trend"] == -66.66666666666666


def test_read_declining_games(app: FastAPI, small_dataset):
    data = small_dataset()

    with TestClient(app) as client:
        response = client.get("boardgames/declining")

    data = response.json()

    assert data[0]["bgg_id"] == 2
    assert data[0]["bgg_rank_trend"] == -66.66666666666666

    assert data[2]["bgg_id"] == 1
    assert data[2]["bgg_rank_trend"] == 66.66666666666666


def test_rank_history_small(app: FastAPI, small_dataset):
    data = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history?page=0")
    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history?page=2&per_page=1")
    data_api = response.json()
    assert response.status_code == 200
    assert data_api[0]["bgg_id"] == 2

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history?compare_to=2025-08-24")
    assert response.status_code == 200

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history?page=1")
    assert response.status_code == 200
    data_api = list(response.json())

    assert len(data_api) == len(data["boardgames"])

    for i, game in enumerate(data["boardgames"]):
        history_entry = data["rank_histories"][2 * i]
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
