import asyncio
import datetime

import pytest

from sabogaapi.api_v1.models import Boardgame

from .conftest import seed_test_data, setup_database


@pytest.mark.slow_integration_test
def test_benchmark_get_top_ranked_boardgames(benchmark):
    async def async_benchmark():
        await setup_database()
        await seed_test_data()
        return await Boardgame.get_top_ranked_boardgames(
            compare_to=datetime.datetime.now(),
            page=1,
            page_size=50,
        )

    def sync_wrapper():
        return asyncio.run(async_benchmark())

    result = benchmark(sync_wrapper)
    assert result
