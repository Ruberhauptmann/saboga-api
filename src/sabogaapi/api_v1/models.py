import datetime
from typing import List

from beanie import BackLink, Document, Link
from pydantic import Field


class Boardgame(Document):
    name: str
    bgg_rating: float | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
    owner: str | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: int | None = None

    plays: List[Link["Play"]] = []

    class Settings:
        name = "boardgames"


class Play(Document):
    playtime_s: int
    rating: float
    points: int
    date: datetime.date
    won: bool
    result_str: str

    games_played: List[BackLink[Boardgame]] = Field(original_field="plays")  # type: ignore

    class Settings:
        name = "plays"
