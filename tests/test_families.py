from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_all_families(app: FastAPI, small_dataset):
    data = small_dataset()
    me_ids = [item.bgg_id for item in data["families"]]

    with TestClient(app) as client:
        response = client.get("/families/")

    assert response.status_code == 200
    api_data = list(response.json())
    assert len(api_data) == len(data["families"])
    assert all([item["bgg_id"] in me_ids for item in api_data])


def test_single_family(app: FastAPI, small_dataset):
    data = small_dataset()
    de_ids = [item.bgg_id for item in data["families"]]

    for i, bgg_id in enumerate(de_ids):
        with TestClient(app) as client:
            response = client.get(f"/families/{bgg_id}")

        assert response.status_code == 200
        api_data = response.json()
        assert data["families"][i].name == api_data["name"]
