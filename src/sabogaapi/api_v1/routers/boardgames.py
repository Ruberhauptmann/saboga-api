import datetime
import math
from itertools import repeat
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response

from sabogaapi.api_v1.models import Boardgame
from sabogaapi.api_v1.schemas import BoardgamePublic

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


def historic_data(game: Boardgame, date: datetime.date) -> Boardgame:
    for entry in reversed(game.bgg_rank_history):
        if entry.date.date() <= date:
            game.bgg_rank = entry.bgg_rank
            game.bgg_average_rating = entry.bgg_average_rating
            game.bgg_average_rating_change = entry.bgg_average_rating_change
            game.bgg_geek_rating = entry.bgg_geek_rating
            game.bgg_geek_rating_change = entry.bgg_geek_rating_change
            return game

    raise HTTPException(
        status_code=404, detail="No historical data available for this day."
    )


@router.get("/", response_model=List[BoardgamePublic])
async def read_all_games(
    response: Response,
    request: Request,
    date: datetime.date = datetime.date.today(),
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
    games = list(map(historic_data, games, repeat(date)))

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
        f'<{request.url_for("read_all_games").include_query_params(page=0, per_page=per_page)}>; rel="first"'
    )

    return games


@router.get("/{game_id}", response_model=BoardgamePublic)
async def read_game(game_id: int) -> Boardgame:
    game = await Boardgame.find(Boardgame.bgg_id == game_id).first_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
