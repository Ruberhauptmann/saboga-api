from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from sabogaapi.database import engine
from sabogaapi.extensions import get_session
from sabogaapi.models import (
    Play,
    PlayCreate,
    PlayRead,
    PlayReadWithBoardgames,
    PlayUpdate,
)

router = APIRouter(
    prefix="/plays",
    tags=["plays"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
@router.get("/", response_model=List[PlayRead])
def read_all_game(
        *, session: Session = Depends(get_session)
) -> Sequence[Play]:
    plays = session.exec(select(Play)).all()
    return plays


@router.post("/", response_model=PlayRead)
def create_play(play: PlayCreate) -> Play:
    with Session(engine) as session:
        db_play = Play.model_validate(play)
        session.add(db_play)
        session.commit()
        session.refresh(db_play)
        return db_play


@router.patch("/{play_id}", response_model=PlayRead)
def update_play(play_id: int, play: PlayUpdate) -> Play:
    with Session(engine) as session:
        db_play = session.get(Play, play_id)
        if not db_play:
            raise HTTPException(status_code=404, detail="Play not found")
        play_data = play.model_dump(exclude_unset=True)
        for key, value in play_data.items():
            setattr(db_play, key, value)
        session.add(db_play)
        session.commit()
        session.refresh(db_play)
        return db_play


@router.delete("/{play_id}")
def delete_play(play_id: int) -> dict[str, bool]:
    with Session(engine) as session:
        play = session.get(Play, play_id)
        if not play:
            raise HTTPException(status_code=404, detail="Play not found")
        session.delete(play)
        session.commit()
        return {"ok": True}


@router.get("/{play_id}", response_model=PlayReadWithBoardgames)
def read_play(*, session: Session = Depends(get_session), play_id: int) -> Play:
    play = session.get(Play, play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    return play
