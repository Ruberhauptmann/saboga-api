from typing import List

from beanie import DeleteRules, PydanticObjectId, WriteRules
from fastapi import APIRouter, HTTPException

from sabogaapi.api_v1.models import Boardgame, Play
from sabogaapi.api_v1.schemas import (
    BoardgameCreate,
    BoardgamePublic,
    BoardgamePublicWithPlays,
    BoardgameUpdate,
)

router = APIRouter(
    prefix="/boardgames",
    tags=["boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgamePublicWithPlays])
async def read_all_games() -> List[Boardgame]:
    games = await Boardgame.find_all(fetch_links=True).to_list()
    return games


@router.post("/", response_model=BoardgamePublic)
async def add_boardgame(boardgame: BoardgameCreate) -> Boardgame:
    boardgame_response = await Boardgame.model_validate(
        boardgame, from_attributes=True
    ).create()
    return boardgame_response


@router.get("/{game_id}", response_model=BoardgamePublicWithPlays)
async def read_game(game_id: PydanticObjectId) -> Boardgame:
    game = await Boardgame.get(game_id, fetch_links=True)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.put("/{game_id}/plays/{play_id}/", response_model=BoardgamePublicWithPlays)
async def add_play_to_boardgame(
    game_id: PydanticObjectId, play_id: PydanticObjectId
) -> Boardgame:
    game = await Boardgame.get(game_id, fetch_links=True)
    play = await Play.get(play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game:
        raise HTTPException(status_code=404, detail="Play not found")
    game.plays = [play]
    await game.save(link_rule=WriteRules.WRITE)
    return game


@router.delete("/{game_id}")
async def delete_game(game_id: PydanticObjectId) -> dict[str, bool]:
    game = await Boardgame.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await game.delete(link_rule=DeleteRules.DO_NOTHING)
    return {"ok": True}


@router.patch("/{game_id}", response_model=BoardgamePublic)
async def update_game(game_id: int, game: BoardgameUpdate) -> Boardgame:
    db_game = await Boardgame.get(game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    game_data = game.model_dump(exclude_unset=True)
    for key, value in game_data.items():
        setattr(db_game, key, value)
    await db_game.save()
    return db_game
