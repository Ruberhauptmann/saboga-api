import datetime

from pydantic import computed_field, field_validator
from sqlmodel import Field, Relationship, SQLModel


class BoardgamePlayLink(SQLModel, table=True):
    boardgame_id: int | None = Field(
        default=None, foreign_key="boardgame.id", primary_key=True
    )
    play_id: int | None = Field(default=None, foreign_key="play.id", primary_key=True)


class PlayBase(SQLModel):
    playtime_s: int
    rating: float
    points: int
    date: datetime.date
    won: bool
    result_str: str


class Play(PlayBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    games_played: list["Boardgame"] = Relationship(
        back_populates="plays", link_model=BoardgamePlayLink
    )


class PlayRead(PlayBase):
    id: int

    @computed_field  # type: ignore
    @property
    def type(self) -> str:
        return "boardgame"

    @computed_field  # type: ignore
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/plays/{self.id}"}


class PlayCreate(PlayBase):
    pass


class PlayUpdate(SQLModel):
    name: str | None = None
    playtime_s: int | None = None
    rating: float | None = None
    points: int | None = None
    date: datetime.date | None = None
    won: bool | None = None
    result_str: str | None = None


class BoardgameBase(SQLModel):
    name: str = Field(index=True)
    bgg_rating: float
    bgg_id: int
    bgg_weight: float
    owner: str
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: int | None = None

    @field_validator(
        "player_min",
        "player_recommended_min",
        "player_max",
        "player_recommended_max",
        mode="before",
    )
    @classmethod
    def parameters_str(cls, v):
        if v == "":
            return None
        return v


class Boardgame(BoardgameBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    plays: list[Play] = Relationship(
        back_populates="games_played", link_model=BoardgamePlayLink
    )


class BoardgameRead(BoardgameBase):
    id: int

    @computed_field  # type: ignore
    @property
    def type(self) -> str:
        return "play"

    @computed_field  # type: ignore
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/boardgames/{self.id}"}


class BoardgameCreate(BoardgameBase):
    pass


class BoardgameUpdate(SQLModel):
    name: str | None = None
    bgg_rating: int | None = None
    bgg_id: int | None
    bgg_weight: float | None
    owner: str | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: None | int = None


class BoardgameReadWithPlays(BoardgameRead):
    plays: list[PlayRead] = []

    @computed_field  # type: ignore
    @property
    def number_of_plays(self) -> int:
        return len(self.plays)

    @computed_field  # type: ignore
    @property
    def number_of_wins(self) -> int:
        return sum(play.won for play in self.plays)

    @computed_field  # type: ignore
    @property
    def win_percentage(self) -> float:
        if self.number_of_plays > 0:
            return self.number_of_wins / self.number_of_plays * 100
        else:
            return 0

    @computed_field  # type: ignore
    @property
    def average_rating(self) -> float:
        if self.number_of_plays > 0:
            return sum(play.rating for play in self.plays) / self.number_of_plays
        else:
            return 0


class PlayReadWithBoardgames(PlayRead):
    games_played: list[BoardgameRead] = []
