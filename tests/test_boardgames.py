from fastapi.testclient import TestClient


def test_rank_history_small(app, small_dataset):
    bg, rh = small_dataset()

    with TestClient(app) as client:
        response = client.get("/boardgames/rank-history")

    assert response.status_code == 200
    data = response.json()
    assert any(item["bgg_id"] == bg.bgg_id for item in data)
