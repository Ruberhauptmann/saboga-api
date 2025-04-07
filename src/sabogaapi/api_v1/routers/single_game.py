import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException

from sabogaapi.api_v1.models import Boardgame, RankHistory
from sabogaapi.api_v1.schemas import BoardgameWithHistoricalData, ForecastData
from sabogaapi.api_v1.statistics.predict import forecast_game_ranking

router = APIRouter(
    prefix="/boardgames/{bgg_id}",
    tags=["Boardgames - Single game"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=BoardgameWithHistoricalData)
async def read_game(
    bgg_id: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    mode: Literal["auto", "daily", "weekly", "yearly"] = "auto",
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
        end_date = datetime.datetime.combine(end_date, datetime.datetime.max.time())
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)
    else:
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    game = await Boardgame.get_boardgame_with_historical_data(
        bgg_id=bgg_id, start_date=start_date, end_date=end_date, mode=mode
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game = BoardgameWithHistoricalData(**game)
    return game


@router.get("/forecast", response_model=ForecastData)
async def forecast(
    bgg_id: int,
) -> ForecastData:
    bgg_rank_history = await RankHistory.find(Boardgame.bgg_id == bgg_id).to_list()
    if not bgg_rank_history:
        raise HTTPException(status_code=404, detail="Game not found")

    prediction = await forecast_game_ranking(bgg_rank_history)

    return ForecastData(
        bgg_id=bgg_id,
        prediction=prediction,
    )


@router.get("/rank-history")
async def rank_history():
    return {"status": "not yet implemented"}


@router.get("/statistics")
async def game_statistics():
    return {"status": "not yet implemented"}


@router.get("/reviews/summary")
async def reviews_summary():
    return {"status": "not yet implemented"}


@router.get("/reviews/sentiment")
async def reviews_sentiment():
    return {"status": "not yet implemented"}


@router.get("/similar")
async def similar_games():
    return {"status": "not yet implemented"}
