import argparse
import asyncio

from sabogaapi.logger import configure_logger

from ._update import ascrape_update

logger = configure_logger()


def scrape() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True)
    args = parser.parse_args()

    match args.mode:
        case "update":
            asyncio.run(ascrape_update())
        case _:
            logger.error(f"Scraper {args.mode} not implemented.")
