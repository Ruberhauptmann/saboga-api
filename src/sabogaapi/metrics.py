from collections.abc import Callable, Coroutine
from typing import Any

from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info
from sqlalchemy import func, select

from sabogaapi import models
from sabogaapi.database import sessionmanager

# Define Prometheus Gauge
LATEST_RANK_HISTORY_TS = Gauge(
    "latest_rank_history_timestamp",
    "Unix timestamp of the most recent entry in rank_history",
)


def latest_rank_history_timestamp() -> Callable[[Info], Coroutine[Any, Any, None]]:
    """Instrumentation that records the latest RankHistory.date as a timestamp."""

    async def instrumentation(_: Info) -> None:
        async with sessionmanager.session() as session:
            stmt = select(func.max(models.RankHistory.date))
            result = await session.execute(stmt)
            latest_date = result.scalar_one_or_none()

            if latest_date is not None:
                # Convert to float (seconds since epoch)
                ts = latest_date.timestamp()
                LATEST_RANK_HISTORY_TS.set(ts)
            else:
                # No data yet, set metric to 0
                LATEST_RANK_HISTORY_TS.set(0.0)

    return instrumentation


instrumentator = Instrumentator().add(latest_rank_history_timestamp())
