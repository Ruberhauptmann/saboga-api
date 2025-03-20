"""Schemas for saboga API."""

import datetime
from typing import List

from pydantic import BaseModel


class RankHistory(BaseModel):
    date: datetime.datetime
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None


class BaseBoardgame(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int
    bgg_geek_rating: float
    bgg_average_rating: float


class BoardgameComparison(BaseBoardgame):
    bgg_rank_change: int
    bgg_geek_rating_change: float
    bgg_average_rating_change: float


class BoardgameWithHistoricalData(BaseBoardgame):
    bgg_rank_history: List[RankHistory]
