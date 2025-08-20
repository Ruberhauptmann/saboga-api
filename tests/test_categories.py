from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_all_categories(app: FastAPI, small_dataset):
    data = small_dataset()
    me_ids = [item.bgg_id for item in data["categories"]]

    with TestClient(app) as client:
        response = client.get("/categories/")

    assert response.status_code == 200
    api_data = list(response.json())
    assert len(api_data) == len(data["categories"])
    assert all([item["bgg_id"] in me_ids for item in api_data])


def test_single_mechanic(app: FastAPI, small_dataset):
    data = small_dataset()
    de_ids = [item.bgg_id for item in data["categories"]]

    for i, bgg_id in enumerate(de_ids):
        with TestClient(app) as client:
            response = client.get(f"/categories/{bgg_id}")

        assert response.status_code == 200
        api_data = response.json()
        assert data["categories"][i].name == api_data["name"]
