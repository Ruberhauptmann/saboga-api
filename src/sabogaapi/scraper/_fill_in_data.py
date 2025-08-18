import asyncio
import html
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any

import aiohttp
import requests
from beanie import WriteRules
from PIL import Image
from pydantic import BaseModel

from sabogaapi import models
from sabogaapi.config import settings
from sabogaapi.database import init_db
from sabogaapi.logger import configure_logger

logger = configure_logger()


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


def _timeout(e: str, number_of_tries: int) -> None:
    waiting_seconds = 2**number_of_tries
    logger.warning("%s. Retrying after %s seconds", e, waiting_seconds)
    time.sleep(waiting_seconds)


def scrape_api(ids: list[int]) -> ET.Element | None:
    number_of_tries = 0
    while number_of_tries < 10:
        try:
            ids_string = ",".join(map(str, ids))
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={ids_string}&stats=1&type=boardgame",
                timeout=10,
            )
            return ET.fromstring(r.text)
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            ET.ParseError,
        ) as e:
            _timeout(repr(e), number_of_tries)
            number_of_tries += 1

    return None


def _extract_rank(ratings: ET.Element | None) -> int | None:
    if ratings is None:
        return None
    rank_element = ratings.find(".//rank[@name='boardgame']")
    return _map_to(int, rank_element.get("value")) if rank_element is not None else None


def _map_to[T](func: Callable[[str], T], value: str | None) -> T | None:
    return None if not value or value == "Not Ranked" else func(value)


def _extract_list(item: ET.Element, key: str) -> list[Any]:
    return_list = []
    for link in item.findall(f".//link[@type='{key}']"):
        element = link.get("value")
        value_id = link.get("id") if element is not None else None
        id_ = int(value_id) if value_id is not None else None
        if element and id_:
            return_list.append((id_, element))
    return return_list


def _extract_int(item: ET.Element, key: str) -> int | None:
    element = item.find(key)
    value = element.get("value") if element is not None else None
    return int(value) if value is not None else None


def parse_boardgame_data(item: ET.Element) -> dict:
    """Extract relevant boardgame data from XML response."""
    bgg_id = int(item.get("id", 0))

    name_element = item.find("name")
    name = None
    if name_element is not None and name_element.get("value"):
        name = _map_to(str, name_element.get("value"))

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
        "name": name,
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


async def analyse_api_response(  # noqa: C901
    item: ET.Element,
) -> tuple[None, None] | tuple[models.Boardgame, list[models.Designer] | None]:
    data = parse_boardgame_data(item)

    # Get boardgame from database or create a new one
    boardgame = await models.Boardgame.find_one(
        models.Boardgame.bgg_id == data["bgg_id"]
    )
    if data["rank"] is None:
        if boardgame is not None:
            await boardgame.delete()
            logger.info("Deleted boardgame %s due to missing rank.", data["bgg_id"])
        return None, None

    if boardgame is None:
        boardgame = models.Boardgame(bgg_id=data["bgg_id"], bgg_rank=data["rank"])

    # Simple fields
    boardgame.name = data["name"]
    boardgame.description = data["description"]
    boardgame.year_published = data["year_published"]
    boardgame.minplayers = data["minplayers"]
    boardgame.maxplayers = data["maxplayers"]
    boardgame.playingtime = data["playingtime"]
    boardgame.minplaytime = data["minplaytime"]
    boardgame.maxplaytime = data["maxplaytime"]

    # Process image
    if data["image_url"]:
        image_filename = f"{data['bgg_id']}.jpg"
        image_file = settings.img_dir / image_filename
        if not image_file.exists():
            async with (
                aiohttp.ClientSession() as session,
                session.get(data["image_url"]) as img_request,
            ):
                if img_request.status == 200:
                    content = await img_request.read()
                    with image_file.open("wb") as handler:
                        handler.write(content)
        thumbnail_filename = f"{image_file.stem}-thumbnail.jpg"
        thumbnail_file = settings.img_dir / thumbnail_filename
        if not thumbnail_file.exists():
            im = Image.open(image_file).convert("RGB")
            im.thumbnail((128, 128))
            im.save(thumbnail_file)

        boardgame.image_url = f"/img/{image_filename}"
        boardgame.thumbnail_url = f"/img/{thumbnail_filename}"

    # Process categories
    category_names_ids = data["categories"]
    if category_names_ids:
        boardgame.categories = [
            models.Category(name=name, bgg_id=bgg_id)
            for bgg_id, name in category_names_ids
        ]

    # Process families
    family_names_ids = data["families"]
    if family_names_ids:
        boardgame.families = [
            models.Family(name=name, bgg_id=bgg_id) for bgg_id, name in family_names_ids
        ]

    # Process mechanics
    mechanic_names_ids = data["mechanics"]
    if mechanic_names_ids:
        boardgame.mechanics = [
            models.Mechanic(name=name, bgg_id=bgg_id)
            for bgg_id, name in mechanic_names_ids
        ]

    # Process designers
    designer_names_ids = data["designers"]
    designers = None
    if designer_names_ids:
        designers = [
            models.Designer(name=name, bgg_id=bgg_id)
            for bgg_id, name in designer_names_ids
        ]

    return boardgame, designers


async def process_designers(designers: list[models.Designer]) -> list[models.Designer]:
    designers_db = []
    for designer in designers:
        existing = await models.Designer.find(
            models.Designer.bgg_id == designer.bgg_id
        ).first_or_none()
        if existing:
            existing.name = designer.name
            await existing.save()
            designers_db.append(existing)
        else:
            new = await models.Designer.insert(designer)
            designers_db.append(new)
    return designers_db


async def process_item(
    item: ET.Element,
) -> models.Boardgame | None:
    boardgame, designers = await analyse_api_response(item)

    if designers:
        designers_db = await process_designers(designers)
    else:
        designers_db = []

    if boardgame:
        boardgame.designers = designers_db  # type: ignore[assignment]
        await boardgame.save(link_rule=WriteRules.DO_NOTHING)
    return None


async def process_batch(ids: list[int]) -> None:
    logger.info("Scraping %s.", ids)
    parsed_xml = scrape_api(ids)
    if parsed_xml is None:
        return

    items = parsed_xml.findall("item")
    for item in items:
        await process_item(item)
    return


async def fill_in_data(step: int = 20) -> None:
    await init_db()
    run_index = 0

    while True:
        ids = (
            await models.Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .sort("-bgg_id")
            .skip(run_index * step)
            .limit(step)
            .to_list()
        )
        ids_int = [x.bgg_id for x in ids]

        if not ids_int:
            break

        await process_batch(ids_int)
        run_index += 1
        await asyncio.sleep(5)
