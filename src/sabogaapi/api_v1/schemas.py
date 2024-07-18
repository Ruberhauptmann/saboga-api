import datetime
from typing import List

from beanie import PydanticObjectId
from pydantic import BaseModel


class BaseBoardgame(BaseModel):
    bgg_id: int
    bgg_rank: List["RatingHistory"]


class RatingHistory(BaseModel):
    date: datetime.datetime
    rank: int
    change: int


class BoardgamePublic(BaseBoardgame):
    id: PydanticObjectId
