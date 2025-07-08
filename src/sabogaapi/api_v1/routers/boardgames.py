"""Routes for viewing the boardgame data."""

import datetime
import math
import time
from typing import List

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import HTTPException

from sabogaapi.api_v1.models import Boardgame
from sabogaapi.api_v1.schemas import BoardgameComparison
from sabogaapi.logger import configure_logger

logger = configure_logger()

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_games():
    return {"status": "not yet implemented"}


@router.get("/rank-history", response_model=List[BoardgameComparison])
async def read_games_with_rank_changes(
    response: Response,
    request: Request,
    compare_to: datetime.date | None = None,
    page: int = 1,
    per_page: int = 50,
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
    start_time = time.time()
    logger.info(
        "Request received",
        extra={
            "params": {
                "page": page,
                "per_page": per_page,
                "compare_to": str(compare_to),
            },
        },
    )

    if page < 1:
        logger.warning(
            "Invalid page number",
            extra={
                "page": page,
            },
        )
        raise HTTPException(
            status_code=422, detail="Page number must be greater than 1"
        )

    if compare_to is None:
        compare_to = datetime.datetime.now() - datetime.timedelta(weeks=1)
        logger.debug(
            "Using default comparison date (1 week ago)",
            extra={
                "compare_to": compare_to.isoformat(),
            },
        )
    else:
        compare_to = datetime.datetime.combine(compare_to, datetime.datetime.min.time())

    compare_to = compare_to.replace(hour=0, minute=0, second=0, microsecond=0)

    top_ranked_data = await Boardgame.get_top_ranked_boardgames(
        compare_to=compare_to, page=page, page_size=per_page
    )
    games = [BoardgameComparison(**game) for game in top_ranked_data]

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

    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "Returning boardgames",
        extra={
            "returned": len(games),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "duration_ms": duration,
        },
    )

    return games


@router.get("/by-category")
async def read_all_games_by_category() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/by-mechanic")
async def read_all_games_by_mechanic() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/by-family")
async def read_all_games_by_family() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/by-designer")
async def read_all_games_by_designer() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/clusters")
async def game_clusters() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/recommendations")
async def recommend_games() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/recommendations/{username}")
async def recommend_games_for_user() -> dict[str, str]:
    return {"status": "not yet implemented"}
