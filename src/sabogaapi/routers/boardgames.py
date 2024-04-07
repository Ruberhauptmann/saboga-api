from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from sabogaapi.database import engine
from sabogaapi.extensions import get_session
from sabogaapi.models import (
    Boardgame,
    BoardgameCreate,
    BoardgameRead,
    BoardgameReadWithPlays,
    BoardgameUpdate, Play,
)

router = APIRouter(
    prefix="/boardgames",
    tags=["boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgameReadWithPlays])
def read_all_game(
    *, session: Session = Depends(get_session)
) -> Sequence[Boardgame]:
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


@router.get("/{game_id}", response_model=BoardgameReadWithPlays)
def read_game(*, session: Session = Depends(get_session), game_id: int) -> Boardgame:
    game = session.get(Boardgame, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.put("/{game_id}/plays/{play_id}")
def add_play_to_game(*, session: Session = Depends(get_session), game_id: int, play_id: int) -> dict[str, bool]:
    game = session.get(Boardgame, game_id)
    play = session.get(Play, play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game:
        raise HTTPException(status_code=404, detail="Play not found")

    game.plays.append(play)
    session.add(game)
    session.commit()

    return {"ok": True}
