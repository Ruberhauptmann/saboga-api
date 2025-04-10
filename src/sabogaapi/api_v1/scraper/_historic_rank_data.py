import datetime
import time
from bisect import bisect_left

import requests
from pydantic import BaseModel

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory
from sabogaapi.logger import configure_logger

logger = configure_logger()


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


def scrape_api(id) -> requests.Response | None:
    payload = {"objectid": id, "objecttype": "thing", "rankobjectid": 1}
    url = "https://api.geekdo.com/api/historicalrankgraph"

    number_of_tries = 0
    while number_of_tries < 10:
        try:
            response = requests.get(url, params=payload)
            return response
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            waiting_seconds = min(2**number_of_tries, 600)
            number_of_tries += 1
            logger.warning(f"Error: {e}, retrying after {waiting_seconds} seconds.")
            time.sleep(waiting_seconds)

    return None


async def update_boardgame_rank_history(
    bgg_id: int, historic_data: list
) -> list[RankHistory]:
    rank_history = (
        await RankHistory.find(RankHistory.bgg_id == bgg_id).sort("-date").to_list()
    )

    if rank_history:
        dates = [datetime.date.fromtimestamp(date / 1000) for date, _ in historic_data]
        oldest_date = rank_history[-1].date.date()
        idx = bisect_left(dates, oldest_date)
    else:
        idx = None

    new_ranks = [
        RankHistory(
            bgg_id=bgg_id,
            date=datetime.datetime.fromtimestamp(date / 1000),
            bgg_rank=int(rank),
        )
        for date, rank in historic_data[:idx]
    ]

    return new_ranks


async def ascrape_historic_rank_data() -> None:
    await init_db()
    ids = await Boardgame.find_all().project(BoardgameBGGIDs).sort("+bgg_id").to_list()
    ids_int = [x.bgg_id for x in ids]

    for id in ids_int:
        print(id, flush=True)
        response = scrape_api(id)
        if response:
            list_of_data = response.json()["data"]
            rank_histories = await update_boardgame_rank_history(
                bgg_id=id, historic_data=list_of_data
            )
            print(f"Inserted {len(rank_histories)} rank histories", flush=True)
            if rank_histories:
                await RankHistory.insert_many(rank_histories)
            time.sleep(0.1)
