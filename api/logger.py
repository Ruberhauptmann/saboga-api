import logging


def configure_logger(name: str = "saboga") -> logging.Logger:
    """Return a logger instance configured for console output.

    This is a very simple stand-in for the previous Loki-based logger used in
    the FastAPI version.  For now it just attaches a stream handler if one does
    not already exist.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
