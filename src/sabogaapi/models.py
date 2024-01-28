from typing import Optional

from sqlmodel import Field, SQLModel


class BoardgameBase(SQLModel):
    name: str = Field(index=True)
    bgg_rating: int
    owner: str
    wishlist: bool
    player_min: int
    player_recommended_min: int
    player_max: int
    player_recommended_max: int


class BoardgameUpdate(SQLModel):
    name: Optional[str] = None
    bgg_rating: Optional[int] = None
    owner: Optional[str] = None
    wishlist: Optional[bool] = None
    player_min: Optional[int] = None
    player_recommended_min: Optional[int] = None
    player_max: Optional[int] = None
    player_recommended_max: Optional[int] = None


class Boardgame(BoardgameBase, table=True):
    game_id: Optional[int] = Field(default=None, primary_key=True)


class BoardgameCreate(BoardgameBase):
    pass


class BoardgameRead(BoardgameBase):
    game_id: int
