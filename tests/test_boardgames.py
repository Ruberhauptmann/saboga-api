from fastapi.testclient import TestClient


def test_rank_history(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/rank-history")
    assert response.status_code == 200


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
