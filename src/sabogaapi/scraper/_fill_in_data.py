import asyncio
import datetime
import xml.etree.ElementTree as ET

import aiohttp
from beanie import WriteRules
from PIL import Image
from pydantic import BaseModel

from sabogaapi import models
from sabogaapi.config import settings
from sabogaapi.database import init_db
from sabogaapi.logger import configure_logger
from sabogaapi.scraper._utilities import parse_boardgame_data, scrape_api

logger = configure_logger()


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


async def analyse_api_response(  # noqa: PLR0915, C901
    item: ET.Element,
) -> (
    tuple[None, None, None]
    | tuple[models.Boardgame, None, list[models.Designer] | None]
    | tuple[models.Boardgame, models.RankHistory, list[models.Designer] | None]
):
    data = parse_boardgame_data(item)

    # Get boardgame from database or create a new one
    boardgame = await models.Boardgame.find_one(
        models.Boardgame.bgg_id == data["bgg_id"]
    )
    if data["rank"] is None:
        if boardgame is not None:
            await boardgame.delete()
            logger.info("Deleted boardgame %s due to missing rank.", data["bgg_id"])
        return None, None, None  # Don't process further

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

    # Process rank history
    last_rank_history = (
        await models.RankHistory.find({"bgg_id": boardgame.bgg_id})
        .sort("-date")
        .limit(1)
        .first_or_none()
    )
    if (
        last_rank_history
        and (datetime.datetime.now(tz=datetime.UTC) - last_rank_history.date).days < 1
    ):
        return boardgame, None, designers

    boardgame.bgg_rank = data["rank"]
    boardgame.bgg_geek_rating = data["geek_rating"]
    boardgame.bgg_average_rating = data["average_rating"]
    rank_history = models.RankHistory(
        bgg_id=boardgame.bgg_id,
        bgg_rank=data["rank"],
        bgg_geek_rating=data["geek_rating"],
        bgg_average_rating=data["average_rating"],
        date=datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        ),
    )

    return boardgame, rank_history, designers


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
    item: ET.Element[str],
) -> tuple[models.Boardgame | None, models.RankHistory | None]:
    boardgame, rank_history, designers = await analyse_api_response(item)

    if designers:
        designers_db = await process_designers(designers)
    else:
        designers_db = []

    if boardgame:
        boardgame.designers = designers_db  # type: ignore[assignment]
        await boardgame.save(link_rule=WriteRules.DO_NOTHING)

    return boardgame, rank_history


async def process_batch(ids: list[int]) -> None:
    logger.info("Scraping %s.", ids)
    parsed_xml = scrape_api(ids)
    if parsed_xml is None:
        return

    items = parsed_xml.findall("item")
    rank_histories = []

    for item in items:
        _, rank_history = await process_item(item)
        if rank_history:
            rank_histories.append(rank_history)

    if rank_histories:
        await models.RankHistory.insert_many(rank_histories)


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
