import time
from datetime import datetime
from xml.etree import ElementTree

import requests
from PIL import Image
from pydantic import BaseModel

from sabogaapi.api_v1.config import settings
from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import (
    Boardgame,
    Category,
    Designer,
    Family,
    Mechanic,
    RankHistory,
)
from sabogaapi.api_v1.scraper._utilities import parse_boardgame_data, scrape_api
from sabogaapi.logger import configure_logger

logger = configure_logger()


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


async def analyse_api_response(
    item: ElementTree.Element,
) -> tuple[None, None] | tuple[Boardgame, None] | tuple[Boardgame, RankHistory]:
    data = parse_boardgame_data(item)

    # Get boardgame from database or create a new one
    boardgame = await Boardgame.find_one(Boardgame.bgg_id == data["bgg_id"])
    if data["rank"] is None:
        if boardgame is not None:
            await boardgame.delete()
            logger.info(f"Deleted boardgame {data['bgg_id']} due to missing rank.")
        return None, None  # Don't process further

    if boardgame is None:
        boardgame = Boardgame(bgg_id=data["bgg_id"])

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
            img_request = requests.get(data["image_url"])
            if img_request.status_code == 200:
                with open(image_file, "wb") as handler:
                    handler.write(img_request.content)

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
            Category(name=name, bgg_id=bgg_id) for bgg_id, name in category_names_ids
        ]

    # Process families
    family_names_ids = data["families"]
    if family_names_ids:
        boardgame.families = [
            Family(name=name, bgg_id=bgg_id) for bgg_id, name in family_names_ids
        ]

    # Process mechanics
    mechanic_names_ids = data["mechanics"]
    if mechanic_names_ids:
        boardgame.mechanics = [
            Mechanic(name=name, bgg_id=bgg_id) for bgg_id, name in mechanic_names_ids
        ]

    # Process designers
    designer_names_ids = data["designers"]
    if designer_names_ids:
        boardgame.designers = [
            Designer(name=name, bgg_id=bgg_id) for bgg_id, name in designer_names_ids
        ]

    # Process rank history
    last_rank_history = (
        await RankHistory.find({"bgg_id": boardgame.bgg_id})
        .sort(-RankHistory.date)
        .limit(1)
        .first_or_none()
    )
    if last_rank_history and (datetime.now() - last_rank_history.date).days < 1:
        return boardgame, None

    boardgame.bgg_rank = data["rank"]
    boardgame.bgg_geek_rating = data["geek_rating"]
    boardgame.bgg_average_rating = data["average_rating"]
    rank_history = RankHistory(
        bgg_id=boardgame.bgg_id,
        bgg_rank=data["rank"],
        bgg_geek_rating=data["geek_rating"],
        bgg_average_rating=data["average_rating"],
        date=datetime.today(),
    )

    return boardgame, rank_history


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
        parsed_xml = scrape_api(ids_int)
        if parsed_xml:
            items = parsed_xml.findall("item")
            rank_histories = []
            for item in items:
                boardgame, rank_history = await analyse_api_response(item)
                if boardgame:
                    await boardgame.save()
                if rank_history:
                    rank_histories.append(rank_history)
            if rank_histories:
                await RankHistory.insert_many(rank_histories)
        run_index += 1
        time.sleep(5)
