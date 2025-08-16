"""Test exceptions."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.integration_test
def test_404(app: FastAPI) -> None:
    """Test 404 route for missing boardgame."""
    with TestClient(app) as client:
        response = client.get("/boardgames/12345")
    assert response.status_code == 404
