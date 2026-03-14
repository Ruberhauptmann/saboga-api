import html
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any

from django.conf import settings

import requests
from PIL import Image

from api import models
from django.core.files.base import ContentFile

from api.logger import configure_logger

logger = configure_logger()


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
                headers={"Authorization": f"Bearer {settings.BGG_API_KEY}"},
            )
            return ET.fromstring(r.text)
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
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
        if element and id_ and not element.startswith("Admin"):
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
    bgg_image_url_element = item.find("image")
    if bgg_image_url_element is not None and bgg_image_url_element.text:
        image_url = bgg_image_url_element.text

    description = None
    description_element = item.find("description")
    if description_element is not None and description_element.text:
        description = html.unescape(description_element.text)

    statistics = item.find("statistics")
    ratings = statistics.find("ratings") if statistics is not None else None
    rank = _extract_rank(ratings)

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
        "rank": rank,
        "description": description,
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


def analyse_api_response(
    item: ET.Element,
) -> tuple[
    models.Boardgame | None,
    list[models.Category],
    list[models.Designer],
    list[models.Family],
    list[models.Mechanic],
]:
    """Parse one <item> and prepare ORM objects (no DB calls)."""
    data = parse_boardgame_data(item)

    if data["rank"] is None:
        return None, [], [], [], []

    # Create boardgame object
    boardgame, _ = models.Boardgame.objects.get_or_create(bgg_id=data["bgg_id"])
    boardgame.name = data["name"]
    boardgame.description = data["description"]
    boardgame.year_published = data["year_published"]
    boardgame.minplayers = data["minplayers"]
    boardgame.maxplayers = data["maxplayers"]
    boardgame.playingtime = data["playingtime"]
    boardgame.minplaytime = data["minplaytime"]
    boardgame.maxplaytime = data["maxplaytime"]

    # Process image
    if data.get("image_url"):
        image_filename = f"{data['bgg_id']}.jpg"
        image_file = settings.MEDIA_ROOT / image_filename
        image_file.parent.mkdir(parents=True, exist_ok=True)

        if not image_file.exists():
            try:
                response = requests.get(data["image_url"], timeout=30)
                content_file = ContentFile(response.content, name=image_filename)
                boardgame.image = content_file
            except requests.RequestException as e:
                logger.warning("Failed to download image for %s: %s", data["bgg_id"], e)

        thumbnail_filename = f"{image_file.stem}-thumbnail.jpg"
        thumbnail_file = settings.MEDIA_ROOT / thumbnail_filename
        if not thumbnail_file.exists():
            im = Image.open(image_file).convert("RGB")
            im.thumbnail((128, 128))
            im.save(thumbnail_file)

        boardgame.image_url = f"/img/{image_filename}"
        boardgame.thumbnail_url = f"/img/{thumbnail_filename}"

    categories = []
    for bgg_id, name in data.get("categories", []):
        category, _ = models.Category.objects.get_or_create(
            bgg_id=bgg_id, defaults={"name": name}
        )
        categories.append(category)

    designers = []
    for bgg_id, name in data.get("designers", []):
        designer, _ = models.Designer.objects.get_or_create(
            bgg_id=bgg_id, defaults={"name": name}
        )
        designers.append(designer)

    families = []
    for bgg_id, name in data.get("families", []):
        family, _ = models.Family.objects.get_or_create(
            bgg_id=bgg_id, defaults={"name": name}
        )
        families.append(family)

    mechanics = []
    for bgg_id, name in data.get("mechanics", []):
        mechanic, _ = models.Mechanic.objects.get_or_create(
            bgg_id=bgg_id, defaults={"name": name}
        )
        mechanics.append(mechanic)

    boardgame.categories.set(categories)
    boardgame.designers.set(designers)
    boardgame.families.set(families)
    boardgame.mechanics.set(mechanics)

    boardgame.save()

    return boardgame


def process_batch(ids: list[int]) -> None:
    logger.info("Scraping %s.", ids)
    parsed_xml = scrape_api(ids)
    if parsed_xml is None:
        return

    for item in parsed_xml.findall("item"):
        analyse_api_response(item)


def run() -> None:
    """Iterate over all known boardgames and refetch details."""
    step = 20

    run_index = 0
    while True:
        ids = models.Boardgame.objects.order_by("-bgg_id").values_list(
            "bgg_id", flat=True
        )[run_index * step : (run_index + 1) * step]
        if not ids:
            break

        process_batch(ids)
        run_index += 1
        time.sleep(5)
