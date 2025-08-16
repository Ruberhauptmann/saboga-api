from collections.abc import Callable, Coroutine
from typing import Any

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info

from sabogaapi.models import Boardgame

# Define Prometheus Gauge
BOARDGAMES_WITHOUT_RANK = Gauge(
    "boardgames_without_recent_rank",
    "Number of board games where the latest bgg_rank is None",
)


def count_games_without_rank() -> (
    Callable[[Info], Coroutine[Any, Any, None]]
):  # pragma: no cover
    """Function returning an instrumentation function that updates the Prometheus metric."""

    async def instrumentation(_: Info) -> None:
        pipeline = [
            {
                "$addFields": {
                    "latest_rank": {
                        "$arrayElemAt": [
                            {
                                "$sortArray": {
                                    "input": "$bgg_rank_history",
                                    "sortBy": {"date": -1},
                                },
                            },
                            0,
                        ],
                    },
                },
            },
            {"$match": {"latest_rank.bgg_rank": None}},
            {"$count": "count"},
        ]

        result = await Boardgame.aggregate(pipeline).to_list()
        count = result[0]["count"] if result else 0

        BOARDGAMES_WITHOUT_RANK.set(count)

    return instrumentation


instrumentator = Instrumentator().add(count_games_without_rank())
