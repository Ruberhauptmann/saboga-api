import logging


def configure_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
