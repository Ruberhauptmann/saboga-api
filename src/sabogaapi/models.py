"""Beanie database models."""

import datetime
from typing import Annotated

from beanie import Document, Indexed, Link, TimeSeriesConfig
from pydantic import BaseModel, Field


class RankHistory(Document):
    date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    bgg_id: int
    bgg_rank: int | None = None
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None

    class Settings:
        timeseries = TimeSeriesConfig(
            time_field="date",
            meta_field="bgg_id",
            bucket_rounding_seconds=86400,
            bucket_max_span_seconds=86400,
        )
        name = "rank_history"


class Category(BaseModel):
    name: str
    bgg_id: int


class Family(BaseModel):
    name: str
    bgg_id: int


class Mechanic(BaseModel):
    name: str
    bgg_id: int


class Designer(Document):
    name: str
    bgg_id: Annotated[int, Indexed(unique=True)]

    class Settings:
        name = "designers"


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed(unique=True)]
    bgg_rank: Annotated[int, Indexed()]
    name: str = ""
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None
    bgg_rank_volatility: float | None = None
    bgg_rank_trend: float | None = None
    bgg_geek_rating_volatility: float | None = None
    bgg_geek_rating_trend: float | None = None
    bgg_average_rating_volatility: float | None = None
    bgg_average_rating_trend: float | None = None
    description: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_published: int | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    categories: list[Category] = []
    families: list[Family] = []
    mechanics: list[Mechanic] = []
    designers: list[Link[Designer]] = []

    class Settings:
        name = "boardgames"
