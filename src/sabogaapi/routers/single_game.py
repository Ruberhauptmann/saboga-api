import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException

from sabogaapi.api.dependencies.core import DBSessionDep
from sabogaapi.schemas import BoardgameSingle, ForecastData
from sabogaapi.services import BoardgameService, RankHistoryService
from sabogaapi.statistics.predict import forecast_game_ranking

router = APIRouter(
    prefix="/boardgames/{bgg_id}",
    tags=["Boardgames - Single game"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_game(
    db_session: DBSessionDep,
    bgg_id: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    mode: Literal["auto", "daily", "weekly", "yearly"] = "auto",
) -> BoardgameSingle:
    """Read a single game for the database.

    Args:
        bgg_id (int): ID.
        start_date (datetime.date | None, optional): Start date for historic date.
            Defaults to None.
        end_date (datetime.date | None, optional): End date for historic date.
            Defaults to None.
        mode (Literal['auto', 'daily', 'weekly', 'yearly'], optional):
            Mode for historic data. Defaults to "auto".

    Raises:
        HTTPException: Exception if no game is found.

    Returns:
        BoardgameSingle: Boardgame.

    Parameters
    ----------
    db_session

    """
    if end_date is None:
        end_date = datetime.datetime.now(tz=datetime.UTC)
    else:
        end_date = datetime.datetime.combine(end_date, datetime.datetime.max.time())
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)
    else:
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    game = await BoardgameService.get_boardgame_with_historical_data(
        db_session=db_session,
        bgg_id=bgg_id,
        start_date=start_date,
        end_date=end_date,
        mode=mode,
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/forecast")
async def forecast(
    db_session: DBSessionDep,
    bgg_id: int,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
) -> ForecastData:
    if end_date is None:
        end_date = datetime.datetime.now(tz=datetime.UTC)
    else:
        end_date = datetime.datetime.combine(end_date, datetime.datetime.max.time())
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)
    else:
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())

    bgg_rank_history = await RankHistoryService.get_rank_history_before_date(
        db_session=db_session,
        bgg_id=bgg_id,
        end_date=end_date,
    )
    if not bgg_rank_history:
        raise HTTPException(status_code=404, detail="Game not found")

    prediction = await forecast_game_ranking(bgg_rank_history)

    return ForecastData(
        bgg_id=bgg_id,
        prediction=prediction,
    )


@router.get("/rank-history")
async def rank_history() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/statistics")
async def game_statistics() -> dict[str, str]:
    return {"status": "not yet implemented"}


@router.get("/similar")
async def similar_games() -> dict[str, str]:
    return {"status": "not yet implemented"}
