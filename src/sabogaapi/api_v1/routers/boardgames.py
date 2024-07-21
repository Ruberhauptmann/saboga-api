import codecs
import csv
import math
import xml.etree.ElementTree as ElementTree
from typing import Annotated, List

import requests
from beanie import PydanticObjectId
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from sabogaapi.api_v1.models import Boardgame
from sabogaapi.api_v1.schemas import BoardgamePublic

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgamePublic])
async def read_all_games(
    response: Response,
    request: Request,
    page: int = 1,
    per_page: int = 100,
) -> List[Boardgame]:
    total_count = await Boardgame.count()
    skip = (page - 1) * per_page
    games = (
        await Boardgame.find({"bgg_rank": {"$type": "int"}})
        .sort("+bgg_rank")
        .skip(skip)
        .limit(per_page)
        .to_list()
    )

    last_page = math.ceil(total_count / per_page)
    response.headers["link"] = ""
    if page > 1:
        response.headers[
            "link"
        ] += f'<{request.url_for("read_all_games").include_query_params(page=page-1, per_page=per_page)}>; rel="prev",'
    if page < last_page:
        response.headers[
            "link"
        ] += f'<{request.url_for("read_all_games").include_query_params(page=page+1, per_page=per_page)}>; rel="next",'
    response.headers["link"] += (
        f'<{request.url_for("read_all_games").include_query_params(page=last_page, per_page=per_page)}>; rel="last",'
        f'<{request.url_for("read_all_games").include_query_params(page=0, per_page=per_page)}>; rel="first",'
    )

    return games


@router.get("/{game_id}", response_model=BoardgamePublic)
async def read_game(game_id: PydanticObjectId) -> Boardgame:
    game = await Boardgame.get(game_id, fetch_links=True)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
