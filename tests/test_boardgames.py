from fastapi.testclient import TestClient


def test_read_boardgames(client: TestClient) -> None:
    response = client.get("/v1/boardgames")
    assert response.status_code == 200
