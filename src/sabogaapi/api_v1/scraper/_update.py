import logging
import time
from datetime import datetime
from typing import Any, Callable
from xml.etree import ElementTree

import requests
from pydantic import BaseModel

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory

logger = logging.getLogger(__name__)


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


def scrape_api(ids: list[int]) -> ElementTree.Element:
    number_of_tries = 0
    while True:
        try:
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(map(str, ids))}&stats=1&type=boardgame"
            )
            return ElementTree.fromstring(r.text)
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            ElementTree.ParseError,
        ) as e:
            waiting_seconds = 2**number_of_tries
            number_of_tries += 1
            logger.warning(f"Error: {e}, retrying after {waiting_seconds} seconds.")
            print(f"Error: {e}, retrying after {waiting_seconds} seconds.", flush=True)
            time.sleep(waiting_seconds)


def _map_to[T](func: Callable[[Any], T], value: str) -> T | None:
    if value == "" or value == "Not Ranked":
        return None
    else:
        return func(value)


async def analyse_api_response(item: ElementTree.Element) -> Boardgame:
    bgg_id = int(item.get("id"))

    statistics = item.find("statistics")
    assert statistics is not None

    ratings = statistics.find("ratings")
    assert ratings is not None

    average_rating_element = ratings.find("average")
    assert average_rating_element is not None
    average_rating_str = average_rating_element.get("value")
    assert average_rating_str is not None
    average_rating = _map_to(float, average_rating_str)

    bayesaverage_rating_element = ratings.find("bayesaverage")
    assert bayesaverage_rating_element is not None
    geek_rating_str = bayesaverage_rating_element.get("value")
    assert geek_rating_str is not None
    geek_rating = _map_to(float, geek_rating_str)

    rank = None
    for rank_element in ratings.iter("rank"):
        if rank_element.attrib["name"] == "boardgame":
            rank_str = rank_element.get("value")
            assert rank_str is not None
            rank = _map_to(int, rank_str)

    boardgame = await Boardgame.find_one(Boardgame.bgg_id == bgg_id)
    if boardgame is None:
        boardgame = Boardgame(bgg_id=bgg_id)

    boardgame.bgg_rank_history.append(
        RankHistory(
            bgg_rank=rank,
            bgg_geek_rating=geek_rating,
            bgg_average_rating=average_rating,
            date=datetime.today(),
        )
    )

    return boardgame


async def ascrape_update(start_id: int, stop_id: int | None, step: int) -> None:
    await init_db()
    run_index = 0
    while True:
        if stop_id is not None and start_id + run_index * step > stop_id:
            break

        ids = (
            await Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .sort("+bgg_id")
            .skip(start_id + run_index * step)
            .limit(step)
            .to_list()
        )
        ids_int: list[int] = list(map(lambda x: x.bgg_id, ids))

        if len(ids) == 0:
            break
        logger.info(f"Scraping {ids}.")
        print(f"Scraping {ids}.", flush=True)
        parsed_xml = scrape_api(ids_int)
        items = parsed_xml.findall("item")
        for item in items:
            boardgame = await analyse_api_response(item)
            await boardgame.save()
        run_index += 1
        time.sleep(5)
