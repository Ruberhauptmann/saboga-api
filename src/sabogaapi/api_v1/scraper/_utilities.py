import html
import logging
import time
from typing import Callable
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)


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
            waiting_seconds = min(2**number_of_tries, 600)
            number_of_tries += 1
            logger.warning(f"Error: {e}, retrying after {waiting_seconds} seconds.")
            print(f"Error: {e}, retrying after {waiting_seconds} seconds.", flush=True)
            time.sleep(waiting_seconds)

    return None


def _extract_rank(ratings: ElementTree.Element | None) -> int | None:
    if ratings is None:
        return None
    rank_element = ratings.find(".//rank[@name='boardgame']")
    return _map_to(int, rank_element.get("value")) if rank_element is not None else None


def _map_to[T](func: Callable[[str], T], value: str | None) -> T | None:
    return None if not value or value == "Not Ranked" else func(value)


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

    year_published_element = item.find("yearpublished")
    year_published_value = (
        year_published_element.get("value")
        if year_published_element is not None
        else None
    )
    year_published = (
        int(year_published_value) if year_published_value is not None else None
    )

    designers = []
    for link in item.findall(".//link[@type='boardgamedesigner']"):
        designer = link.get("value")
        if designer:
            designers.append(designer)

    categories = []
    for link in item.findall(".//link[@type='boardgamecategory']"):
        category = link.get("value")
        category_value_id = link.get("id") if category is not None else None
        category_id = int(category_value_id) if category_value_id is not None else None
        if category and category_id:
            categories.append((category_id, category))

    mechanics = []
    for link in item.findall(".//link[@type='boardgamemechanic']"):
        mechanic = link.get("value")
        mechanic_value_id = link.get("id") if mechanic is not None else None
        mechanic_id = int(mechanic_value_id) if mechanic_value_id is not None else None
        if mechanic and mechanic_id:
            mechanics.append((mechanic_id, mechanic))

    return {
        "bgg_id": bgg_id,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "description": description,
        "rank": rank,
        "average_rating": average_rating,
        "geek_rating": geek_rating,
        "year_published": year_published,
        "categories": categories,
        "mechanics": mechanics,
        "designers": designers,
    }
