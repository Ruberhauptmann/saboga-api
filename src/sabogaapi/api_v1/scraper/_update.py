import html
import logging
import time
from datetime import datetime
from typing import Any, Callable
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
    bgg_id = int(item.get("id", 0))

    boardgame = await Boardgame.find_one(Boardgame.bgg_id == bgg_id)
    if boardgame is None:
        boardgame = Boardgame(bgg_id=bgg_id)

    bgg_image_url_element = item.find("image")
    if bgg_image_url_element is not None:
        bgg_image_url = bgg_image_url_element.text
        assert bgg_image_url is not None

        image_filename = f"{bgg_id}.jpg"
        image_url = f"/img/{image_filename}"
        image_file = IMG_DIR / image_filename
        if not image_file.exists():
            img_request = requests.get(bgg_image_url)
            if img_request.status_code == 200:
                img_data = requests.get(bgg_image_url).content
                with open(f"{image_file}", "wb") as handler:
                    handler.write(img_data)

        thumbnail_filename = f"{image_file.stem}-thumbnail.jpg"
        thumbnail_url = f"/img/{thumbnail_filename}"
        thumbnail_file = IMG_DIR / thumbnail_filename
        if not thumbnail_file.exists():
            im = Image.open(image_file).copy().convert("RGB")
            im.thumbnail((128, 128))
            im.save(thumbnail_file)

        boardgame.image_url = image_url
        boardgame.thumbnail_url = thumbnail_url

    description_element = item.find("description")
    assert description_element is not None
    description_text = description_element.text
    assert description_text is not None
    description = html.unescape(description_text)
    boardgame.description = description

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

    if boardgame.bgg_rank_history:
        last_history = boardgame.bgg_rank_history[-1]
        sync_difference = datetime.now() - last_history.date
        if sync_difference.days < 1:
            return boardgame

    boardgame.bgg_rank_history.append(
        RankHistory(
            bgg_rank=rank,
            bgg_geek_rating=geek_rating,
            bgg_average_rating=average_rating,
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
        ids_int: list[int] = list(map(lambda x: x.bgg_id, ids))

        if len(ids) == 0:
            break
        logger.info(f"Scraping {ids}.")
        print(f"Scraping {ids}.", flush=True)
        parsed_xml = scrape_api(ids_int)
        items = parsed_xml.findall("item")
        for item in items:
            boardgame = await analyse_api_response(item)
            if boardgame.bgg_rank_history[-1].bgg_rank is None:
                await boardgame.delete()
            else:
                await boardgame.save()
        run_index += 1
        time.sleep(5)
