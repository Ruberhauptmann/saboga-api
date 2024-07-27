"""Schemas for saboga API."""
from beanie import PydanticObjectId
from pydantic import BaseModel


class BaseBoardgame(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int
    bgg_rank_change: int
    bgg_geek_rating: float
    bgg_geek_rating_change: float
    bgg_average_rating: float
    bgg_average_rating_change: float


class BoardgamePublic(BaseBoardgame):
    id: PydanticObjectId
