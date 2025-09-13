"""Beanie database models."""

import datetime
from typing import Annotated, Literal

from beanie import BackLink, Document, Indexed, Link, TimeSeriesConfig
from pydantic import Field


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
    mean_trend: float | None = None
    description: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_published: int | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    categories: list[Link["Category"]] = []
    families: list[Link["Family"]] = []
    mechanics: list[Link["Mechanic"]] = []
    designers: list[Link["Designer"]] = []
    type: Literal["boardgame"] = "boardgame"

    class Settings:
        name = "boardgames"


class Category(Document):
    name: str
    bgg_id: Annotated[int, Indexed(unique=True)]
    boardgames: list[BackLink["Boardgame"]] = Field(
        json_schema_extra={"original_field": "categories"}, default=[]
    )
    type: Literal["category"] = "category"

    class Settings:
        name = "categories"


class Designer(Document):
    name: str
    bgg_id: Annotated[int, Indexed(unique=True)]
    boardgames: list[BackLink["Boardgame"]] = Field(
        json_schema_extra={"original_field": "designers"}, default=[]
    )
    type: Literal["designer"] = "designer"

    class Settings:
        name = "designers"


class DesignerNetwork(Document):
    nodes: list[dict]
    edges: list[dict]

    class Settings:
        name = "designer_network"


class Family(Document):
    name: str
    bgg_id: Annotated[int, Indexed(unique=True)]
    boardgames: list[BackLink["Boardgame"]] = Field(
        json_schema_extra={"original_field": "families"}, default=[]
    )
    type: Literal["family"] = "family"

    class Settings:
        name = "families"


class Mechanic(Document):
    name: str
    bgg_id: Annotated[int, Indexed(unique=True)]
    boardgames: list[BackLink["Boardgame"]] = Field(
        json_schema_extra={"original_field": "mechanics"}, default=[]
    )
    type: Literal["mechanic"] = "mechanic"

    class Settings:
        name = "mechanics"


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
