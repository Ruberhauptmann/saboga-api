from datetime import datetime
from typing import List

from beanie import PydanticObjectId
from pydantic import BaseModel


class BaseBoardgame(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None
    bgg_rank_history: List["RankHistory"]


class RankHistory(BaseModel):
    date: datetime
    bgg_rank: int | None
    bgg_rank_change: int | None
    bgg_geek_rating: float | None
    bgg_geek_rating_change: float | None
    bgg_average_rating: float | None
    bgg_average_rating_change: float | None


class BoardgamePublic(BaseBoardgame):
    id: PydanticObjectId
