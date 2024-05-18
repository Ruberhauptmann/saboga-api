import datetime
from typing import List, Optional

from beanie import BackLink, Document, Link
from fastapi_users.db import BeanieBaseUser
from pydantic import Field


class User(BeanieBaseUser, Document):
    role: str = "user"


class Boardgame(Document):
    name: str
    bgg_rating: float | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
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
    date: datetime.date
    won: bool
    user: Link[User] | None = None

    # games_played: List[BackLink[Boardgame]] = Field(original_field="plays")  # type: ignore

    class Settings:
        name = "plays"
