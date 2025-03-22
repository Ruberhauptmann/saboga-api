import html
import logging
import time
from datetime import datetime
from typing import Callable
from xml.etree import ElementTree

import requests
from PIL import Image
from pydantic import BaseModel

from sabogaapi.api_v1.config import IMG_DIR
from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory

logger = logging.getLogger(__name__)


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


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
    """Extract boardgame rank efficiently."""
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

    return {
        "bgg_id": bgg_id,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "description": description,
        "rank": rank,
        "average_rating": average_rating,
        "geek_rating": geek_rating,
    }


async def analyse_api_response(item: ElementTree.Element) -> Boardgame | None:
    data = parse_boardgame_data(item)

    boardgame = await Boardgame.find_one(Boardgame.bgg_id == data["bgg_id"])
    if data["rank"] is None:
        if boardgame:
            await boardgame.delete()
            logger.info(f"Deleted boardgame {data['bgg_id']} due to missing rank.")
        return None  # Don't process further

    if boardgame is None:
        boardgame = Boardgame(bgg_id=data["bgg_id"])

    boardgame.description = data["description"]

    if data["image_url"]:
        image_filename = f"{data['bgg_id']}.jpg"
        image_file = IMG_DIR / image_filename
        if not image_file.exists():
            img_request = requests.get(data["image_url"])
            if img_request.status_code == 200:
                with open(image_file, "wb") as handler:
                    handler.write(img_request.content)

        thumbnail_filename = f"{image_file.stem}-thumbnail.jpg"
        thumbnail_file = IMG_DIR / thumbnail_filename
        if not thumbnail_file.exists():
            im = Image.open(image_file).convert("RGB")
            im.thumbnail((128, 128))
            im.save(thumbnail_file)

        boardgame.image_url = f"/img/{image_filename}"
        boardgame.thumbnail_url = f"/img/{thumbnail_filename}"

    if boardgame.bgg_rank_history:
        last_history = boardgame.bgg_rank_history[-1]
        if (datetime.now() - last_history.date).days < 1:
            return boardgame

    boardgame.bgg_rank_history.append(
        RankHistory(
            bgg_rank=data["rank"],
            bgg_geek_rating=data["geek_rating"],
            bgg_average_rating=data["average_rating"],
            date=datetime.today(),
        )
    )

    return boardgame


async def ascrape_update(start_id: int, step: int) -> None:
    await init_db()
    run_index = 0
    while True:
        ids = (
            await Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .sort("+bgg_id")
            .skip(start_id + run_index * step)
            .limit(step)
            .to_list()
        )
        ids_int = [x.bgg_id for x in ids]

        if len(ids) == 0:
            break
        logger.info(f"Scraping {ids_int}.")
        print(f"Scraping {ids_int}.", flush=True)
        parsed_xml = scrape_api(ids_int)
        if parsed_xml:
            items = parsed_xml.findall("item")
            for item in items:
                boardgame = await analyse_api_response(item)
                if boardgame:
                    await boardgame.save()
        run_index += 1
        time.sleep(5)
