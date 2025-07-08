import logging

from asgi_correlation_id import CorrelationIdFilter
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("loki_logger")
    logger.setLevel(logging.DEBUG)

    logger.propagate = False

    loki_handler = LokiLoggerHandler(
        url="http://loki:3100/loki/api/v1/push",
        labels={"application": "Saboga"},
        label_keys={},
        timeout=10,
    )
    loki_handler.addFilter(CorrelationIdFilter(uuid_length=32, default_value="-"))
    logger.addHandler(loki_handler)

    return logger
