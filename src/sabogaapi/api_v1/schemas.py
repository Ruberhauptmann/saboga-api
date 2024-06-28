import datetime
from typing import Any, List, Optional

from beanie import PydanticObjectId
from fastapi_users import schemas
from fastapi_users.schemas import model_dump
from pydantic import BaseModel, computed_field


class BaseBoardgame(BaseModel):
    name: str
    bgg_rating: float | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: int | None = None


class BasePlay(BaseModel):
    playtime_s: int
    rating: float
    date: datetime.date
    won: bool


class BaseCollection(BaseModel):
    name: str


class BaseResults(BaseModel):
    player_name: str
    points: Optional[float] = None
    position: Optional[int] = None
    is_winner: bool


class PlayPublic(BasePlay):
    id: PydanticObjectId
    user: Optional["UserRead"]

    @computed_field  # type: ignore
    @property
    def type(self) -> str:
        return "play"

    @computed_field  # type: ignore
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/plays/{self.id}"}


class PlayCreate(BasePlay):
    pass


class PlayUpdate(BaseModel):
    playtime_s: int | None = None
    rating: float | None = None
    date: datetime.date | None = None
    won: bool | None = None


class PlayPublicWithBoardgames(PlayPublic):
    games_played: List["BoardgamePublic"] = []


class BoardgamePublic(BaseBoardgame):
    id: PydanticObjectId

    @computed_field  # type: ignore
    @property
    def type(self) -> str:
        return "boardgame"

    @computed_field  # type: ignore
    @property
    def link(self) -> dict[str, str]:
        return {"self": f"/boardgames/{self.id}"}


class BoardgamePublicWithPlays(BoardgamePublic):
    plays: List[PlayPublic] = []

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


class BoardgameCreate(BaseBoardgame):
    pass


class BoardgameUpdate(BaseModel):
    name: str | None = None
    bgg_rating: int | None = None
    bgg_id: int | None = None
    bgg_weight: float | None = None
    player_min: int | None = None
    player_recommended_min: int | None = None
    player_max: int | None = None
    player_recommended_max: None | int = None


class CollectionPublic(BaseCollection):
    id: PydanticObjectId
    user: "UserRead"
    games: List[BoardgamePublic] = []


class CollectionCreate(BaseCollection):
    pass


class CollectionUpdate(BaseModel):
    name: str | None = None


class ResultsPublic(BaseResults):
    id: PydanticObjectId
    player: Optional["UserRead"] = None
    games_played: List["BoardgamePublic"] = []


class UserRead(schemas.BaseUser[PydanticObjectId]):
    id: PydanticObjectId
    role: str = "user"


class UserCreate(schemas.BaseUserCreate):
    role: str = "user"

    def create_update_dict(self) -> dict[str, Any]:
        return model_dump(
            self,
            exclude_unset=True,
            exclude={
                "id",
                "is_superuser",
                "is_active",
                "is_verified",
                "oauth_accounts",
                "role",
            },
        )

    def create_update_dict_superuser(self) -> dict[str, Any]:
        return model_dump(self, exclude_unset=True, exclude={"id"})


class UserUpdate(schemas.BaseUserUpdate):
    role: str

    def create_update_dict(self) -> dict[str, Any]:
        return model_dump(
            self,
            exclude_unset=True,
            exclude={
                "id",
                "is_superuser",
                "is_active",
                "is_verified",
                "oauth_accounts",
                "role",
            },
        )

    def create_update_dict_superuser(self) -> dict[str, Any]:
        return model_dump(self, exclude_unset=True, exclude={"id"})
