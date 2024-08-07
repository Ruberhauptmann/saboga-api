import logging
import time
from typing import Any, Callable
from xml.etree import ElementTree

import requests
from pydantic import BaseModel

from sabogaapi.api_v1.models import Boardgame

logger = logging.getLogger(__name__)


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


def scrape_api(ids: list[int]) -> str:
    number_of_tries = 0
    while True:
        try:
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(map(str, ids))}&stats=1&type=boardgame"
            )
            return r.text
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
        ) as e:
            waiting_seconds = 2**number_of_tries
            number_of_tries += 1
            logger.warning(f"Error: {e}, retrying after {waiting_seconds} seconds.")
            time.sleep(waiting_seconds)


def _map_to(func: Callable[[Any], Any], value: str) -> Any | None:
    if value == "":
        return None
    else:
        return func(value)


async def analyse_api_response(item: ElementTree.Element) -> Boardgame:
    bgg_id = int(item.get("id"))
    ratings = item.find("statistics").find("ratings")
    average_rating = _map_to(float, ratings.find("average").get("value"))
    geek_rating = _map_to(float, ratings.find("bayesaverage").get("value"))
    rank = None
    for rank_element in ratings.iter("rank"):
        if rank_element.attrib["name"] == "boardgame":
            rank = _map_to(int, rank_element.get("value"))

    boardgame = await Boardgame.find_one(Boardgame.bgg_id == bgg_id)
    if boardgame is None:
        boardgame = Boardgame(bgg_id=bgg_id)

    boardgame.bgg_rank = rank
    boardgame.bgg_geek_rating = geek_rating
    boardgame.bgg_average_rating = average_rating

    if rank is not None and average_rating is not None and geek_rating is not None:
        boardgame.bgg_rank_change = boardgame.bgg_rank - rank
        boardgame.bgg_average_rating_change = round(
            average_rating - boardgame.bgg_average_rating, 5
        )
        boardgame.bgg_geek_rating_change = round(
            geek_rating - boardgame.bgg_geek_rating, 5
        )

    return boardgame


async def ascrape_update(start_id: int, stop_id: int, step: int) -> None:
    run_index = 0
    while True:
        if start_id + run_index * step > stop_id:
            break
        ids = (
            await Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .sort("+bgg_id")
            .skip(start_id + run_index * step)
            .limit(step)
            .to_list()
        )
        ids = list(map(lambda x: x.bgg_id, ids))
        if len(ids) == 0:
            break
        logger.info(f"Scraping {ids}.")
        raw_xml = scrape_api(ids)
        try:
            parsed_xml = ElementTree.fromstring(raw_xml)
            items = parsed_xml.findall("item")
            for item in items:
                boardgame = await analyse_api_response(item)
                if (
                    boardgame.bgg_rank is None
                    or boardgame.bgg_geek_rating is None
                    or boardgame.bgg_average_rating is None
                ):
                    await boardgame.delete()
                else:
                    await boardgame.save()
        except ElementTree.ParseError as e:
            logger.error(f"Error parsing xml: {e}, trying next batch.")
        run_index += 1
