from datetime import datetime
from typing import Annotated, List

from beanie import Document, Indexed
from pydantic import BaseModel


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed()]
    name: str | None = None
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None
    bgg_rank: List["RatingHistory"] = []
    last_data_sync: datetime | None = None

    class Settings:
        name = "boardgames"


class BoardgameSettings(Document):
    last_bgg_ranking_scrape: datetime
    last_bgg_scrape_page: int
    max_bgg_scrape: int = 100

    class Settings:
        name = "boardgames.settings"


class RatingHistory(BaseModel):
    date: datetime
    rank: int
    change: int
