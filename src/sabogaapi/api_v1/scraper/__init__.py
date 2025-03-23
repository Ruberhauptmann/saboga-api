import argparse
import asyncio

from ._update import ascrape_update


def scrape() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action=argparse.BooleanOptionalAction)
    parser.add_argument("--step", type=int, default=20)
    args = parser.parse_args()

    if args.full is True:
        print("Full scraper not implemented.", flush=True)
    else:
        asyncio.run(ascrape_update(step=args.step))
