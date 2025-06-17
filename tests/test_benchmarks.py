import asyncio
import datetime

import pytest

from sabogaapi.api_v1.models import Boardgame


@pytest.mark.slow_integration_test
def test_benchmark_get_top_ranked_boardgames(benchmark, app):
    async def benchmark_get_top_ranked_boardgames():
        return await Boardgame.get_top_ranked_boardgames(
            compare_to=datetime.datetime.now(),
            page=1,
            page_size=50,
        )

    def async_wrapper():
        return asyncio.run(benchmark_get_top_ranked_boardgames())

    result = benchmark(async_wrapper)
    assert result
