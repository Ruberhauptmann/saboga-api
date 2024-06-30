import datetime
from typing import List, Optional

from beanie import Document, Link
from fastapi_users.db import BeanieBaseUser


class User(BeanieBaseUser, Document):
    role: str = "user"


class Collection(Document):
    name: str
    user: Optional[Link[User]] = None
    games: List[Link["Boardgame"]] = []

    class Settings:
        name = "collections"


class Boardgame(Document):
    name: str
    bgg_rating: float | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: int | None = None

    class Settings:
        name = "boardgames"


class Result(Document):
    player_name: str
    player: Optional[Link[User]] = None
    points: Optional[float] = None
    position: Optional[int] = None
    is_winner: bool

    class Settings:
        name = "results"


class Play(Document):
    playtime_s: int
    rating: float
    date: datetime.date
    user: Link[User] | None = None
    results: List[Result] = []
    games_played: List[Link[Boardgame]] = []

    class Settings:
        name = "plays"
