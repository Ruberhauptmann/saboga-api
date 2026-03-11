"""Schemas for saboga API."""

import datetime

from pydantic import BaseModel


class BaseBoardgame(BaseModel):
    bgg_id: int
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_published: int | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    bgg_rank: int
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None
    bgg_rank_trend: float | None = None
    bgg_geek_rating_trend: float | None = None
    bgg_average_rating_trend: float | None = None
    mean_trend: float | None = None

    class Config:
        from_attributes = True


class BoardgameInList(BaseBoardgame):
    bgg_rank_change: int | None = None
    bgg_geek_rating_change: float | None = None
    bgg_average_rating_change: float | None = None

    class Config:
        from_attributes = True


class BoardgameSingle(BaseBoardgame):
    categories: list["Category"] = []
    families: list["Family"] = []
    designers: list["Designer"] = []
    mechanics: list["Mechanic"] = []
    bgg_rank_history: list["RankHistory"] = []

    class Config:
        from_attributes = True


class BaseCategory(BaseModel):
    name: str
    bgg_id: int

    class Config:
        from_attributes = True


class Category(BaseCategory):
    class Config:
        from_attributes = True


class CategoryWithBoardgames(BaseCategory):
    boardgames: list["BoardgameInList"]

    class Config:
        from_attributes = True


class BaseDesigner(BaseModel):
    name: str
    bgg_id: int

    class Config:
        from_attributes = True


class Designer(BaseDesigner):
    class Config:
        from_attributes = True


class DesignerWithBoardgames(BaseDesigner):
    boardgames: list["BoardgameInList"]

    class Config:
        from_attributes = True


class BaseFamily(BaseModel):
    name: str
    bgg_id: int

    class Config:
        from_attributes = True


class Family(BaseFamily):
    class Config:
        from_attributes = True


class FamilyWithBoardgames(BaseFamily):
    boardgames: list["BoardgameInList"]

    class Config:
        from_attributes = True


class RankHistory(BaseModel):
    date: datetime.date
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None

    class Config:
        from_attributes = True


class BaseMechanic(BaseModel):
    name: str
    bgg_id: int

    class Config:
        from_attributes = True


class Mechanic(BaseMechanic):
    class Config:
        from_attributes = True


class MechanicWithBoardgames(BaseMechanic):
    boardgames: list["BoardgameInList"]

    class Config:
        from_attributes = True


class Prediction(BaseModel):
    date: datetime.date
    bgg_rank: int
    bgg_rank_confidence_interval: tuple[float, float]
    bgg_average_rating: float
    bgg_average_rating_confidence_interval: tuple[float, float]
    bgg_geek_rating: float
    bgg_geek_rating_confidence_interval: tuple[float, float]

    class Config:
        from_attributes = True


class ForecastData(BaseModel):
    bgg_id: int
    prediction: list[Prediction]

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    bgg_id: int
    name: str
    type: str

    class Config:
        from_attributes = True


class Node(BaseModel):
    id: str
    label: str
    x: float
    y: float
    size: float
    cluster: int

    class Config:
        from_attributes = True


class Edge(BaseModel):
    id: str
    label: str
    source: str
    target: str
    size: float

    class Config:
        from_attributes = True


class Network(BaseModel):
    nodes: list[Node]
    edges: list[Edge]

    class Config:
        from_attributes = True
