import pytest
from fastapi.testclient import TestClient


@pytest.mark.slow_integration_test
def test_read_boardgames(app, benchmark) -> None:
    def benchmark_function():
        return client.get("v1/boardgames/rank-history")

    with TestClient(app) as client:
        response = benchmark(benchmark_function)
    assert response.status_code == 200
