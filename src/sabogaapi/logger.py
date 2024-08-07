import logging


def configure_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        filename="app.log",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
