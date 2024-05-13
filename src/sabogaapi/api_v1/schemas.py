import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, computed_field


class BaseBoardgame(BaseModel):
    name: str
    bgg_rating: float | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
    owner: str | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: int | None = None


class BoardgameCreate(BaseBoardgame):
    pass


class BoardgamePublic(BaseBoardgame):
    id: PydanticObjectId

    @computed_field
    @property
    def type(self) -> str:
        return "boardgame"

    @computed_field
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/boardgames/{self.id}"}


class BasePlay(BaseModel):
    playtime_s: int
    rating: float
    points: int
    date: datetime.date
    won: bool
    result_str: str


class PlayPublic(BasePlay):
    id: PydanticObjectId

    @computed_field
    @property
    def type(self) -> str:
        return "play"

    @computed_field
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/plays/{self.id}"}


class PlayCreate(BasePlay):
    pass


class PlayUpdate(BaseModel):
    name: str | None = None
    playtime_s: int | None = None
    rating: float | None = None
    points: int | None = None
    date: datetime.date | None = None
    won: bool | None = None
    result_str: str | None = None


class BoardgameUpdate(BaseModel):
    name: str | None = None
    bgg_rating: int | None = None
    bgg_id: int | None
    bgg_weight: float | None
    owner: str | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: None | int = None


class BoardgamePublicWithPlays(BoardgamePublic):
    plays: list[PlayPublic] = []

    @computed_field
    @property
    def number_of_plays(self) -> int:
        return len(self.plays)

    @computed_field
    @property
    def number_of_wins(self) -> int:
        return sum(play.won for play in self.plays)

    @computed_field
    @property
    def win_percentage(self) -> float:
        if self.number_of_plays > 0:
            return self.number_of_wins / self.number_of_plays * 100
        else:
            return 0

    @computed_field
    @property
    def average_rating(self) -> float:
        if self.number_of_plays > 0:
            return sum(play.rating for play in self.plays) / self.number_of_plays
        else:
            return 0


class PlayPublicWithBoardgames(PlayPublic):
    games_played: list[BoardgamePublic] = []
