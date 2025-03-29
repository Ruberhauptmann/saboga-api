import argparse
import asyncio

from sabogaapi.logger import configure_logger

from ._historic_rank_data import ascrape_historic_rank_data
from ._rank_history_to_ts import convert_rank_history_to_ts
from ._update import ascrape_update

logger = configure_logger()


def scrape() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True)
    parser.add_argument("--step", type=int, default=20, required=False)
    args = parser.parse_args()

    match args.mode:
        case "update":
            asyncio.run(ascrape_update(step=args.step))
        case "historic-ranks":
            asyncio.run(ascrape_historic_rank_data())
        case "convert-rank-history":
            asyncio.run(convert_rank_history_to_ts())
        case _:
            logger.error(f"Scraper {args.mode} not implemented.")
