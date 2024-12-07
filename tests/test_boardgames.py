from fastapi.testclient import TestClient


def test_read_boardgames(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames")
    assert response.status_code == 200
