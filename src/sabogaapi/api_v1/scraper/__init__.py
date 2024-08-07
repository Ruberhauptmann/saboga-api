import argparse
import asyncio

from ..database import init_db
from ._full import ascrape_full
from ._update import ascrape_update


def scrape() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action=argparse.BooleanOptionalAction)
    parser.add_argument("--step", type=int)
    parser.add_argument("--start", type=int)
    parser.add_argument("--stop", type=int)
    args = parser.parse_args()

    asyncio.run(init_db())

    if args.full is True:
        asyncio.run(ascrape_full(step=args.step))
    else:
        asyncio.run(
            ascrape_update(step=args.step, start_id=args.start, stop_id=args.stop)
        )
