from fastapi.testclient import TestClient


def test_root(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames")
    assert response.status_code == 200
    assert response.json() == {"status": "not yet implemented"}


def test_rank_history(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/rank-history")
    assert response.status_code == 200

    with TestClient(app) as client:
        response = client.get("/v1/boardgames/rank-history", params={"page": "0"})
    assert response.status_code == 422


def test_single_game(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/1234")
    assert response.status_code == 404


def test_single_game_forecast(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/1234/forecast")
    assert response.status_code == 404


def test_volatile(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/volatile")
    assert response.status_code == 200


def test_clusters(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/clusters")
    assert response.status_code == 200
    assert response.json() == {"status": "not yet implemented"}


def test_recommendations(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/recommendations")
    assert response.status_code == 200
    assert response.json() == {"status": "not yet implemented"}


def test_recommendations_username(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/recommendations/test")
    assert response.status_code == 200
    assert response.json() == {"status": "not yet implemented"}
