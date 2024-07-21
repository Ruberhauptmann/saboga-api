from datetime import datetime
from typing import Annotated, List

from beanie import Document, Indexed, ValidateOnSave, after_event
from pydantic import BaseModel


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed(unique=True)]
    name: str
    bgg_rank: int | None
    bgg_rank_change: int | None
    bgg_geek_rating: float | None
    bgg_geek_rating_change: float | None
    bgg_average_rating: float | None
    bgg_average_rating_change: float | None
    bgg_rank_history: List["RankHistory"] = []
    last_data_sync: datetime | None = None

    @after_event(ValidateOnSave)
    def update_rank_history(self) -> None:
        self.bgg_rank_history.append(
            RankHistory(
                date=datetime.now(),
                bgg_rank=self.bgg_rank,
                bgg_rank_change=self.bgg_rank_change,
                bgg_geek_rating=self.bgg_geek_rating,
                bgg_geek_rating_change=self.bgg_geek_rating_change,
                bgg_average_rating=self.bgg_average_rating,
                bgg_average_rating_change=self.bgg_average_rating_change,
            )
        )
        self.last_data_sync = datetime.now()

    class Settings:
        name = "boardgames"


class BoardgameSettings(Document):
    last_bgg_scrape: datetime
    last_scraped_id: int

    class Settings:
        name = "boardgames.settings"


class RankHistory(BaseModel):
    date: datetime
    bgg_rank: int | None
    bgg_rank_change: int | None
    bgg_geek_rating: float | None
    bgg_geek_rating_change: float | None
    bgg_average_rating: float | None
    bgg_average_rating_change: float | None
