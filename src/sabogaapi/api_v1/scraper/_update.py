import logging
import time
from datetime import datetime
from xml.etree import ElementTree

import requests
from PIL import Image
from pydantic import BaseModel

from sabogaapi.api_v1.config import IMG_DIR
from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, Category, Mechanic, RankHistory
from sabogaapi.api_v1.scraper._utilities import parse_boardgame_data, scrape_api

logger = logging.getLogger(__name__)


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


async def analyse_api_response(item: ElementTree.Element) -> Boardgame | None:
    data = parse_boardgame_data(item)

    print(data, flush=True)

    # Get boardgame from database or create a new one
    boardgame = await Boardgame.find_one(Boardgame.bgg_id == data["bgg_id"])
    if data["rank"] is None:
        if boardgame:
            await boardgame.delete()
            logger.info(f"Deleted boardgame {data['bgg_id']} due to missing rank.")
        return None  # Don't process further

    if boardgame is None:
        boardgame = Boardgame(bgg_id=data["bgg_id"])

    # Simple fields
    boardgame.description = data["description"]
    boardgame.year_published = data["year_published"]

    # Process image
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

    # Process categories
    category_names_ids = data["categories"]
    boardgame.categories = [
        Category(name=name, bgg_id=bgg_id) for bgg_id, name in category_names_ids
    ]

    # Process mechanics
    mechanic_names_ids = data["mechanics"]
    boardgame.mechanics = [
        Mechanic(name=name, bgg_id=bgg_id) for bgg_id, name in mechanic_names_ids
    ]

    # Process rank history
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


async def ascrape_update(step: int) -> None:
    await init_db()
    run_index = 0
    while True:
        ids = (
            await Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .sort("-bgg_id")
            .skip(run_index * step)
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
