import html
import logging
import time
from typing import Callable
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)


def _timeout(e: str, number_of_tries: int) -> None:
    waiting_seconds = min(2**number_of_tries, 0.1)
    logger.warning(f"Error: {e}, retrying after {waiting_seconds} seconds.")
    time.sleep(waiting_seconds)


def scrape_api(ids: list[int]) -> ElementTree.Element | None:
    number_of_tries = 0
    while number_of_tries < 10:
        try:
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(map(str, ids))}&stats=1&type=boardgame",
                timeout=10,
            )
            return ElementTree.fromstring(r.text)
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            ElementTree.ParseError,
        ) as e:
            _timeout(e, number_of_tries)
            number_of_tries += 1

    return None


def _extract_rank(ratings: ElementTree.Element | None) -> int | None:
    if ratings is None:
        return None
    rank_element = ratings.find(".//rank[@name='boardgame']")
    return _map_to(int, rank_element.get("value")) if rank_element is not None else None


def _map_to[T](func: Callable[[str], T], value: str | None) -> T | None:
    return None if not value or value == "Not Ranked" else func(value)


def _extract_list(item: ElementTree.Element, key: str):
    return_list = []
    for link in item.findall(f".//link[@type='{key}']"):
        element = link.get("value")
        value_id = link.get("id") if element is not None else None
        id_ = int(value_id) if value_id is not None else None
        if element and id_:
            return_list.append((id_, element))
    return return_list


def _extract_int(item: ElementTree.Element, key: str) -> int | None:
    element = item.find(key)
    value = element.get("value") if element is not None else None
    value_int = int(value) if value is not None else None
    return value_int


def parse_boardgame_data(item: ElementTree.Element) -> dict:
    """Extract relevant boardgame data from XML response."""
    bgg_id = int(item.get("id", 0))

    image_url = None
    thumbnail_url = None
    bgg_image_url_element = item.find("image")
    if bgg_image_url_element is not None and bgg_image_url_element.text:
        image_url = bgg_image_url_element.text

    description = None
    description_element = item.find("description")
    if description_element is not None and description_element.text:
        description = html.unescape(description_element.text)

    # Ranking Data Extraction
    statistics = item.find("statistics")
    ratings = statistics.find("ratings") if statistics is not None else None
    rank = _extract_rank(ratings)
    average_element = ratings.find("average") if ratings is not None else None
    average_rating = (
        _map_to(float, average_element.get("value"))
        if average_element is not None
        else None
    )
    geek_element = ratings.find("bayesaverage") if ratings is not None else None
    geek_rating = (
        _map_to(float, geek_element.get("value")) if geek_element is not None else None
    )

    year_published = _extract_int(item, "yearpublished")
    minplayers = _extract_int(item, "minplayers")
    maxplayers = _extract_int(item, "maxplayers")
    playingtime = _extract_int(item, "playingtime")
    minplaytime = _extract_int(item, "minplaytime")
    maxplaytime = _extract_int(item, "maxplaytime")

    designers = _extract_list(item, "boardgamedesigner")
    categories = _extract_list(item, "boardgamecategory")
    mechanics = _extract_list(item, "boardgamemechanic")
    families = _extract_list(item, "boardgamefamily")

    return {
        "bgg_id": bgg_id,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "description": description,
        "rank": rank,
        "average_rating": average_rating,
        "geek_rating": geek_rating,
        "year_published": year_published,
        "minplayers": minplayers,
        "maxplayers": maxplayers,
        "playingtime": playingtime,
        "minplaytime": minplaytime,
        "maxplaytime": maxplaytime,
        "categories": categories,
        "families": families,
        "mechanics": mechanics,
        "designers": designers,
    }
