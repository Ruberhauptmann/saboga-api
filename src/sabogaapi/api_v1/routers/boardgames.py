"""Routes for viewing the boardgame data."""

import datetime
import math
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response

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
    date: str | None = None,
    compare_to: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> List[BoardgamePublic]:
    """Returns a list of boardgames from the database, sorted by rank.

    \f
    Parameters
    ----------
    response (Response): FastAPI response object, to inject the link header in the reponse.
    request (Request): FastAPI request object, to parse the url for linking to the boardgame overview
        in the link header.
    date (str): Date in YEAR/WEEK format, search for historical data on this date.
    compare_to (str): Date in YEAR/WEEK format, to compare boardgame ranking data against.
    page (int, optional): Number of page for pagination.
    per_page (int, optional): Number of records per page for pagination.

    Returns
    -------
    List[BoardgamePublic]: List of boardgames from the database.

    """

    if date is None:
        date = datetime.date.today().strftime("%Y/%W")
    top_ranked_data = await Boardgame.get_top_ranked_boardgames(
        week_year=date, compare_to=compare_to, page=page, page_size=per_page
    )

    games = [BoardgamePublic(**game.dict()) for game in top_ranked_data]

    total_count = await Boardgame.find_all().count()
    last_page = math.ceil(total_count / per_page)
    response.headers["link"] = ""
    if page > 1:
        response.headers["link"] += (
            f'<{request.url_for("read_all_games").include_query_params(page=page - 1, per_page=per_page)}>; rel="prev",'
        )
    if page < last_page:
        response.headers["link"] += (
            f'<{request.url_for("read_all_games").include_query_params(page=page + 1, per_page=per_page)}>; rel="next",'
        )
    response.headers["link"] += (
        f'<{request.url_for("read_all_games").include_query_params(page=last_page, per_page=per_page)}>; rel="last",'
        f'<{request.url_for("read_all_games").include_query_params(page=1, per_page=per_page)}>; rel="first"'
    )

    return games


@router.get("/{bgg_id}", response_model=BoardgamePublic)
async def read_game(bgg_id: int) -> Boardgame:
    """Returns a single board game from the database.

    \f
    Parameters
    ----------
    bgg_id (int): The Boardgamegeek id of the board game.

    Returns
    -------
    Boardgame: The board game from the database.

    """
    game = await Boardgame.find(Boardgame.bgg_id == bgg_id).first_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
