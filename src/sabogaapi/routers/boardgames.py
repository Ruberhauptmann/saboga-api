"""Routes for viewing the boardgame data."""

import datetime
import math
import time

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import HTTPException

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import BoardgameInList, Network
from sabogaapi.services import BoardgameService

logger = configure_logger()

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_games() -> dict[str, str]:
    return {"status": "not yet implemented"}


def make_link(request: Request, page: int, per_page: int, rel: str) -> str:
    url = request.url_for("read_all_games").include_query_params(
        page=page, per_page=per_page
    )
    return f'<{url}>; rel="{rel}"'


@router.get("/rank-history")
async def read_games_with_rank_changes(
    response: Response,
    request: Request,
    compare_to: datetime.date | None = None,
    page: int = 1,
    per_page: int = 50,
) -> list[BoardgameInList]:
    """Return a list of boardgames from the database, sorted by rank.

    \f

    Parameters
    ----------
    response (Response): FastAPI response object, to inject the link header in the
        reponse.
    request (Request): FastAPI request object, to parse the url for linking to the
        boardgame overview in the link header.
    date (str): Date in YEAR/WEEK format, search for historical data on this date.
    compare_to (str): Date in YEAR/WEEK format, to compare boardgame
        ranking data against.
    page (int, optional): Number of page for pagination.
    per_page (int, optional): Number of records per page for pagination.

    Returns
    -------
    List[BoardgameComparison]: List of boardgames from the database.

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
            status_code=422,
            detail="Page number must be greater than 1",
        )

    if compare_to is None:
        compare_to = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
            weeks=1
        )
        logger.debug(
            "Using default comparison date (1 week ago)",
            extra={
                "compare_to": compare_to.isoformat(),
            },
        )
    else:
        compare_to = datetime.datetime.combine(compare_to, datetime.datetime.min.time())

    compare_to = compare_to.replace(hour=0, minute=0, second=0, microsecond=0)

    top_ranked_data = await BoardgameService.get_top_ranked_boardgames(
        compare_to=compare_to,
        page=page,
        page_size=per_page,
    )

    total_count = await BoardgameService.get_total_count()
    last_page = math.ceil(total_count / per_page)

    links = []
    if page > 1:
        links.append(make_link(request, page - 1, per_page, "prev"))
    if page < last_page:
        links.append(make_link(request, page + 1, per_page, "next"))
    links.extend(
        [
            make_link(request, last_page, per_page, "last"),
            make_link(request, 1, per_page, "first"),
        ]
    )
    response.headers["link"] = ", ".join(links)

    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "Returning boardgames",
        extra={
            "returned": len(top_ranked_data),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "duration_ms": duration,
        },
    )
    return top_ranked_data


@router.get("/volatile")
async def read_games_with_volatility() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/trending")
async def read_trending_games() -> list[BoardgameInList]:
    return await BoardgameService.get_trending_games(limit=5)


@router.get("/declining")
async def read_declining_games() -> list[BoardgameInList]:
    return await BoardgameService.get_declining_games(limit=5)


@router.get("/clusters")
async def read_boardgame_clusters() -> Network:
    return await BoardgameService.get_boardgame_network()
