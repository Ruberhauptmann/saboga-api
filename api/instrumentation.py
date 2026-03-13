from prometheus_client import Gauge
from django.db.models import Max
from django.utils.deprecation import MiddlewareMixin

from . import models

# gauge used by both the DRF endpoint and the middleware
LATEST_RANK_HISTORY_TS = Gauge(
    "latest_rank_history_timestamp",
    "Unix timestamp of the most recent entry in rank_history",
)


class RankHistoryMiddleware(MiddlewareMixin):
    """Middleware that refreshes our custom gauge and records request
    duration on every request.

    django_prometheus already exposes `/metrics` for us; the middleware
    simply updates the values in the shared registry.  the summary metric
    is equivalent to the decorator pattern you showed, but here we
    update it globally instead of wrapping a single function.
    """

    def process_response(self, request, response):
        max_date = models.RankHistory.objects.aggregate(max_date=Max("updated_at"))[
            "max_date"
        ]
        if max_date is not None:
            LATEST_RANK_HISTORY_TS.set(max_date.timestamp())
        else:
            LATEST_RANK_HISTORY_TS.set(0.0)
        return response
