"""Schemas for saboga API."""

import datetime

from pydantic import BaseModel


class RankHistory(BaseModel):
    date: datetime.date
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None


class BaseCategory(BaseModel):
    name: str
    bgg_id: int


class Category(BaseCategory):
    pass


class CategoryWithBoardgames(BaseCategory):
    boardgames: list["BoardgameInList"]


class BaseFamily(BaseModel):
    name: str
    bgg_id: int


class Family(BaseFamily):
    pass


class FamilyWithBoardgames(BaseFamily):
    boardgames: list["BoardgameInList"]


class BaseDesigner(BaseModel):
    name: str
    bgg_id: int


class Designer(BaseDesigner):
    pass


class DesignerWithBoardgames(BaseDesigner):
    boardgames: list["BoardgameInList"]


class BaseMechanic(BaseModel):
    name: str
    bgg_id: int


class Mechanic(BaseMechanic):
    pass


class MechanicWithBoardgames(BaseMechanic):
    boardgames: list["BoardgameInList"]


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


class BoardgameInList(BaseBoardgame):
    bgg_rank_change: int | None = None
    bgg_geek_rating_change: float | None = None
    bgg_average_rating_change: float | None = None


class BoardgameSingle(BaseBoardgame):
    categories: list[Category] = []
    families: list[Family] = []
    designers: list[Designer] = []
    mechanics: list[Mechanic] = []
    bgg_rank_history: list[RankHistory] = []


class Prediction(BaseModel):
    date: datetime.date
    bgg_rank: int
    bgg_rank_confidence_interval: tuple[float, float]
    bgg_average_rating: float
    bgg_average_rating_confidence_interval: tuple[float, float]
    bgg_geek_rating: float
    bgg_geek_rating_confidence_interval: tuple[float, float]


class ForecastData(BaseModel):
    bgg_id: int
    prediction: list[Prediction]


class SearchResult(BaseModel):
    bgg_id: int
    name: str


class DesignerNode(BaseModel):
    id: str
    label: str
    x: float
    y: float
    size: float
    cluster: int


class DesignerEdge(BaseModel):
    id: str
    label: str
    source: str
    target: str
    size: float


class DesignerNetwork(BaseModel):
    nodes: list[DesignerNode]
    edges: list[DesignerEdge]
