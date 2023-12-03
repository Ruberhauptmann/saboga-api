from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from sabogaapi.database import engine
from sabogaapi.models import Boardgame, BoardgameRead

router = APIRouter(
    prefix="/games",
    tags=["games"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[BoardgameRead])
def read_games() -> list[Boardgame]:
    with Session(engine) as session:
        games = session.exec(select(Boardgame)).all()
        return games


@router.get("/{game_id}", response_model=BoardgameRead)
def read_item(game_id: int) -> Boardgame:
    with Session(engine) as session:
        game = session.get(Boardgame, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
