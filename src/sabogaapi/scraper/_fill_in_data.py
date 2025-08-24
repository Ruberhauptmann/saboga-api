import asyncio
import html
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any, TypeVar

import aiohttp
import community as community_louvain
import networkx as nx
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


def graph_to_dict(graph: nx.Graph) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": str(n),
                "label": graph.nodes[n].get("label", str(n)),
                "x": graph.nodes[n]["x"],
                "y": graph.nodes[n]["y"],
                "size": graph.nodes[n]["size"],
                "cluster": graph.nodes[n]["cluster"],
            }
            for n in graph.nodes
        ],
        "edges": [
            {
                "id": f"{u}-{v}",
                "label": d["label"],
                "source": str(u),
                "target": str(v),
                "size": d["size"],
            }
            for u, v, d in graph.edges(data=True)
        ],
    }


def build_designer_graph(
    boardgames: list[models.Boardgame], designers: list[models.Designer]
) -> nx.Graph:
    graph = nx.Graph()

    for d in designers:
        graph.add_node(d.bgg_id, label=d.name)

    for g in boardgames:
        d_ids = [d.bgg_id for d in g.designers]  # type: ignore[attr-defined]
        for i in range(len(d_ids)):
            for j in range(i + 1, len(d_ids)):
                if graph.has_edge(d_ids[i], d_ids[j]):
                    graph[d_ids[i]][d_ids[j]]["weight"] += 1
                else:
                    graph.add_edge(d_ids[i], d_ids[j], weight=1)

    # Clustering
    partition = community_louvain.best_partition(graph, weight="weight")
    for n in graph.nodes:
        if graph.degree[n] == 0:
            partition[n] = -1  # isolated nodes

    pos = nx.spring_layout(graph, seed=42, weight="weight", k=0.5)

    centrality = nx.betweenness_centrality(graph)

    for n, data in graph.nodes(data=True):
        data["x"] = float(pos[n][0])
        data["y"] = float(pos[n][1])
        data["size"] = centrality.get(n, 0) * 30 + 5
        data["cluster"] = partition[n]

    for _u, _v, data in graph.edges(data=True):
        data["size"] = data.get("weight", 1)
        data["label"] = str(data.get("weight", 1))

    return graph


async def construct_designer_network() -> nx.Graph:
    """Construct a graph from designer data."""
    boardgames = await models.Boardgame.find({}, fetch_links=True).to_list()
    designers = await models.Designer.find().to_list()
    return build_designer_graph(boardgames, designers)


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
) -> (
    tuple[None, None, None, None, None]
    | tuple[
        models.Boardgame,
        list[models.Category] | None,
        list[models.Designer] | None,
        list[models.Family] | None,
        list[models.Mechanic] | None,
    ]
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
        return None, None, None, None, None

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
    categories = None
    if category_names_ids:
        categories = [
            models.Category(name=name, bgg_id=bgg_id)
            for bgg_id, name in category_names_ids
        ]

    # Process families
    family_names_ids = data["families"]
    families = None
    if family_names_ids:
        families = [
            models.Family(name=name, bgg_id=bgg_id) for bgg_id, name in family_names_ids
        ]

    # Process mechanics
    mechanic_names_ids = data["mechanics"]
    mechanics = None
    if mechanic_names_ids:
        mechanics = [
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

    return boardgame, categories, designers, families, mechanics


T = TypeVar("T", bound=models.Document)


async def process_entities(
    entities: list[T],
    model: type[T],
    id_field: str = "bgg_id",
    update_fields: list[str] | None = None,
) -> list[T | None]:
    """
    Insert or update entities of a given model.

    Args:
        entities: List of model instances to process.
        model: The model class (e.g., models.Designer).
        id_field: The unique field used for lookup (default "bgg_id").
        update_fields: Fields to update if entity exists. Defaults to all.

    Returns:
        List of entities as stored in the database.
    """
    entities_db = []
    for entity in entities:
        entity_id = getattr(entity, id_field)
        existing = await model.find(
            getattr(model, id_field) == entity_id
        ).first_or_none()

        fields_to_update = update_fields or [
            f for f in entity.model_dump() if f != id_field
        ]

        if existing:
            update_dict = {field: getattr(entity, field) for field in fields_to_update}
            await model.find(getattr(model, id_field) == entity_id).update(
                {"$set": update_dict}
            )
            existing = await model.find(
                getattr(model, id_field) == entity_id
            ).first_or_none()
            entities_db.append(existing)
        else:
            new = await model.insert(entity)
            entities_db.append(new)

    return entities_db


async def process_item(
    item: ET.Element,
) -> models.Boardgame | None:
    boardgame, categories, designers, families, mechanics = await analyse_api_response(
        item
    )

    if categories:
        categories_db = await process_entities(
            model=models.Category, entities=categories
        )
    else:
        categories_db = []
    if designers:
        designers_db = await process_entities(model=models.Designer, entities=designers)
    else:
        designers_db = []
    if families:
        families_db = await process_entities(model=models.Family, entities=families)
    else:
        families_db = []
    if mechanics:
        mechanics_db = await process_entities(model=models.Mechanic, entities=mechanics)
    else:
        mechanics_db = []

    if boardgame:
        boardgame.categories = categories_db  # type: ignore[assignment]
        boardgame.designers = designers_db  # type: ignore[assignment]
        boardgame.families = families_db  # type: ignore[assignment]
        boardgame.mechanics = mechanics_db  # type: ignore[assignment]
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

    graph = await construct_designer_network()
    await models.DesignerNetwork.delete_all()
    graph_db = models.DesignerNetwork(**graph_to_dict(graph))
    await graph_db.insert()
