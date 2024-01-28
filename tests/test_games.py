from fastapi.testclient import TestClient


def test_games_all(client: TestClient):
    response = client.get("/games")
    print(response.json())
    assert response.status_code == 200
    assert False
