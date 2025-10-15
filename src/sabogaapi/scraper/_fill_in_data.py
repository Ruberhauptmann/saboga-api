import asyncio
import html
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any, TypeVar

import aiohttp
import requests
from PIL import Image
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from sabogaapi import models
from sabogaapi.config import settings
from sabogaapi.database import AsyncSession, Base, sessionmanager
from sabogaapi.logger import configure_logger
from sabogaapi.statistics.clusters import (
    construct_category_network,
    construct_designer_network,
    construct_family_network,
    construct_mechanic_network,
    graph_to_dict,
)

logger = configure_logger()


T = TypeVar("T", bound=models.Base)


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


async def analyse_api_response(
    item: ET.Element, session: AsyncSession
) -> tuple[
    models.Boardgame | None,
    list[models.Category],
    list[models.Designer],
    list[models.Family],
    list[models.Mechanic],
]:
    """Parse one <item> and prepare ORM objects (no DB calls)."""
    data = parse_boardgame_data(item)

    # Unranked games → skip (handled later by caller)
    if data["rank"] is None:
        return None, [], [], [], []

    # Create boardgame object
    boardgame = models.Boardgame(bgg_id=data["bgg_id"], bgg_rank=data["rank"])
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
        image_file = settings.img_dir / image_filename
        image_file.parent.mkdir(parents=True, exist_ok=True)

        if not image_file.exists():
            async with (
                aiohttp.ClientSession() as session_img,
                session_img.get(data["image_url"]) as resp,
            ):
                if resp.status == 200:
                    content = await resp.read()
                    with image_file.open("wb") as f:
                        f.write(content)

        thumbnail_filename = f"{image_file.stem}-thumbnail.jpg"
        thumbnail_file = settings.img_dir / thumbnail_filename
        if not thumbnail_file.exists():
            im = Image.open(image_file).convert("RGB")
            im.thumbnail((128, 128))
            im.save(thumbnail_file)

        boardgame.image_url = f"/img/{image_filename}"
        boardgame.thumbnail_url = f"/img/{thumbnail_filename}"

    categories = []
    for bgg_id, name in data.get("categories", []):
        category = await get_or_create(
            session, models.Category, bgg_id=bgg_id, defaults={"name": name}
        )
        categories.append(category)

    designers = []
    for bgg_id, name in data.get("designers", []):
        designer = await get_or_create(
            session, models.Designer, bgg_id=bgg_id, defaults={"name": name}
        )
        designers.append(designer)

    families = []
    for bgg_id, name in data.get("families", []):
        family = await get_or_create(
            session, models.Family, bgg_id=bgg_id, defaults={"name": name}
        )
        families.append(family)

    mechanics = []
    for bgg_id, name in data.get("mechanics", []):
        mechanic = await get_or_create(
            session, models.Mechanic, bgg_id=bgg_id, defaults={"name": name}
        )
        mechanics.append(mechanic)

    return boardgame, categories, designers, families, mechanics


async def get_or_create(
    session: AsyncSession,
    model: type[T],
    defaults: dict[str, Any] | None = None,
    **kwargs: dict[str, Any],
) -> T:
    stmt = select(model).filter_by(**kwargs)
    instance = await session.scalar(stmt)
    if instance:
        return instance

    params = {**kwargs}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        instance = await session.scalar(stmt)

    return instance


async def process_entities(
    session: AsyncSession,
    entities: list[Any],
    model: type[Any],
    id_field: str = "bgg_id",
    update_fields: list[str] | None = None,
) -> list[Any]:
    results = []

    for entity in entities:
        entity_id = getattr(entity, id_field)
        stmt = select(model).where(getattr(model, id_field) == entity_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        # exclude primary key column
        fields_to_update = update_fields or [
            f.name
            for f in entity.__table__.columns
            if f.name not in (id_field, "id", "type")
        ]

        if existing:
            for f in fields_to_update:
                setattr(existing, f, getattr(entity, f))
            results.append(existing)
        else:
            session.add(entity)
            results.append(entity)

    await session.flush()
    return results


async def process_item(
    session: AsyncSession, item: ET.Element
) -> models.Boardgame | None:
    boardgame, categories, designers, families, mechanics = await analyse_api_response(
        item=item, session=session
    )
    if not boardgame:
        return None

    # Add all child entities to session and flush to get PKs
    all_children = categories + designers + families + mechanics
    for child in all_children:
        session.add(child)
    await session.flush()

    # Load boardgame with relationships to avoid lazy loading
    stmt = (
        select(models.Boardgame)
        .where(models.Boardgame.bgg_id == boardgame.bgg_id)
        .options(
            selectinload(models.Boardgame.categories),
            selectinload(models.Boardgame.designers),
            selectinload(models.Boardgame.families),
            selectinload(models.Boardgame.mechanics),
        )
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    skip_fields = {"id", "type"}
    if existing:
        # Update simple columns
        for f in boardgame.__table__.columns:
            if f not in skip_fields:
                setattr(existing, f, getattr(boardgame, f))
        # Assign relationships directly (objects are already in session)
        existing.categories = categories
        existing.designers = designers
        existing.families = families
        existing.mechanics = mechanics
    else:
        # Add new boardgame and assign relationships
        boardgame.categories = categories
        boardgame.designers = designers
        boardgame.families = families
        boardgame.mechanics = mechanics
        session.add(boardgame)

    await session.commit()
    return boardgame


async def process_batch(session: AsyncSession, ids: list[int]) -> None:
    logger.info("Scraping %s.", ids)
    parsed_xml = scrape_api(ids)
    if parsed_xml is None:
        return

    for item in parsed_xml.findall("item"):
        await process_item(session, item)


async def fill_in_data(step: int = 20) -> None:
    """Iterate over all known boardgames and refetch details."""

    async with sessionmanager.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmanager.session() as session:
        run_index = 0
        while True:
            result = await session.execute(
                select(models.Boardgame.bgg_id)
                .order_by(models.Boardgame.bgg_id.desc())
                .offset(run_index * step)
                .limit(step)
            )
            ids = [r[0] for r in result.all()]
            if not ids:
                break

            await process_batch(session, ids)
            run_index += 1
            await asyncio.sleep(5)

        await session.execute(delete(models.CategoryNetwork))
        await session.commit()

        category_graph = await construct_category_network()
        network = models.CategoryNetwork(**graph_to_dict(category_graph))
        session.add(network)
        await session.commit()

        await session.execute(delete(models.DesignerNetwork))
        await session.commit()

        designer_graph = await construct_designer_network()
        network = models.DesignerNetwork(**graph_to_dict(designer_graph))
        session.add(network)
        await session.commit()

        await session.execute(delete(models.FamilyNetwork))
        await session.commit()

        family_graph = await construct_family_network()
        network = models.FamilyNetwork(**graph_to_dict(family_graph))
        session.add(network)
        await session.commit()

        await session.execute(delete(models.MechanicNetwork))
        await session.commit()

        mechanic_graph = await construct_mechanic_network()
        network = models.MechanicNetwork(**graph_to_dict(mechanic_graph))
        session.add(network)
        await session.commit()
