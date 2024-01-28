from typing import List, Sequence

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from sabogaapi.database import engine
from sabogaapi.models import Boardgame, BoardgameRead, BoardgameCreate, BoardgameUpdate

router = APIRouter(
    prefix="/games",
    tags=["games"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
@router.get("/", response_model=List[BoardgameRead])
def read_all_games() -> Sequence[Boardgame]:
    with Session(engine) as session:
        games = session.exec(select(Boardgame)).all()
        return games


@router.post("/", response_model=BoardgameRead)
def create_game(game: BoardgameCreate) -> Boardgame:
    with Session(engine) as session:
        db_game = Boardgame.model_validate(game)
        session.add(db_game)
        session.commit()
        session.refresh(db_game)
        return db_game


@router.patch("/{game_id}", response_model=BoardgameRead)
def update_game(game_id: int, game: BoardgameUpdate) -> Boardgame:
    with Session(engine) as session:
        db_game = session.get(Boardgame, game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")
        game_data = game.model_dump(exclude_unset=True)
        for key, value in game_data.items():
            setattr(db_game, key, value)
        session.add(db_game)
        session.commit()
        session.refresh(db_game)
        return db_game


@router.delete("/{game_id}")
def delete_game(game_id: int) -> dict[str, bool]:
    with Session(engine) as session:
        game = session.get(Boardgame, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        session.delete(game)
        session.commit()
        return {"ok": True}


@router.get("/{game_id}", response_model=BoardgameRead)
def read_game(game_id: int) -> Boardgame:
    with Session(engine) as session:
        game = session.get(Boardgame, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
