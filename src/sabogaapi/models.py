from typing import Optional

from sqlmodel import Field, SQLModel


class BoardgameBase(SQLModel):
    name: str
    bgg_rating: int


class Boardgame(BoardgameBase, table=True):
    game_id: Optional[int] = Field(default=None, primary_key=True)


class BoardgameCreate(BoardgameBase):
    pass


class BoardgameRead(BoardgameBase):
    game_id: int
