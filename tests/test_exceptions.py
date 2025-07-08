import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration_test
def test_404(app) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/boardgames/12345")
    assert response.status_code == 404
