"""Schemas for saboga API."""

import datetime
from typing import List

from pydantic import BaseModel


class RankHistory(BaseModel):
    date: datetime.datetime
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None


class Category(BaseModel):
    name: str
    bgg_id: int


class Person(BaseModel):
    name: str
    bgg_id: int


class Mechanic(BaseModel):
    name: str
    bgg_id: int


class BaseBoardgame(BaseModel):
    bgg_id: int
    name: str
    description: str | None
    image_url: str | None
    thumbnail_url: str | None
    year_published: int | None
    minplayers: int | None
    maxplayers: int | None
    playingtime: int | None
    minplaytime: int | None
    maxplaytime: int | None
    categories: List[Category]
    designers: List[Person]
    mechanics: List[Mechanic]
    bgg_rank: int
    bgg_geek_rating: float
    bgg_average_rating: float


class BoardgameComparison(BaseBoardgame):
    bgg_rank_change: int
    bgg_geek_rating_change: float
    bgg_average_rating_change: float


class BoardgameWithHistoricalData(BaseBoardgame):
    bgg_rank_history: List[RankHistory]


class Prediction(BaseModel):
    date: datetime.date
    rank_prediction: int
    rank_confidence_interval: tuple[float, float]


class ForecastData(BaseModel):
    bgg_id: int
    game_name: str
    prediction: List[Prediction]
