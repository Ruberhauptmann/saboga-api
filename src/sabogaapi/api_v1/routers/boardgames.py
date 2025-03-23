"""Routes for viewing the boardgame data."""

import datetime
import math
from typing import List
from zipfile import ZipFile

import pandas as pd
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile

from sabogaapi.api_v1.models import Boardgame
from sabogaapi.api_v1.schemas import BoardgameComparison, BoardgameWithHistoricalData

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgameComparison])
async def read_all_games(
    response: Response,
    request: Request,
    date: datetime.date | None = None,
    compare_to: datetime.date | None = None,
    page: int = 1,
    per_page: int = 100,
) -> List[BoardgameComparison]:
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
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.combine(date, datetime.datetime.min.time())
    if compare_to is None:
        compare_to = date - datetime.timedelta(weeks=1)
    else:
        compare_to = datetime.datetime.combine(compare_to, datetime.datetime.min.time())

    top_ranked_data = await Boardgame.get_top_ranked_boardgames(
        date=date, compare_to=compare_to, page=page, page_size=per_page
    )

    games = [BoardgameComparison(**game.dict()) for game in top_ranked_data]

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


@router.get("/{bgg_id}", response_model=BoardgameWithHistoricalData)
async def read_game(
    bgg_id: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    mode: str = "auto",
) -> Boardgame:
    """Returns a single board game from the database.

    \f
    Parameters
    ----------
    bgg_id (int): The Boardgamegeek id of the board game.

    Returns
    -------
    Boardgame: The board game from the database.

    """
    if end_date is None:
        end_date = datetime.datetime.now()
    else:
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)
    else:
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    game = await Boardgame.get_boardgame_with_historical_data(
        bgg_id=bgg_id, start_date=start_date, end_date=end_date, mode=mode
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/uploadfile/")
async def create_upload_file(csv_zip_file: UploadFile) -> dict[str, str]:
    with ZipFile(csv_zip_file.file) as csv_zip:
        with csv_zip.open("boardgames_ranks.csv") as rank_csv_file:
            df = pd.read_csv(rank_csv_file)[lambda x: x["rank"] != 0]

    new_ids = df["id"]
    existing_ids = {
        doc.bgg_id async for doc in Boardgame.find({"bgg_id": {"$in": new_ids}})
    }
    unique_ids = [Boardgame(bgg_id=id_) for id_ in new_ids if id_ not in existing_ids]

    if unique_ids:
        await Boardgame.insert_many(unique_ids)

    return {"success": "ok"}
