from typing import List

from beanie import DeleteRules, PydanticObjectId, WriteRules
from fastapi import APIRouter, Depends, HTTPException

from sabogaapi.api_v1.models import Boardgame, Play, User
from sabogaapi.api_v1.schemas import (
    BoardgameCreate,
    BoardgamePublic,
    BoardgamePublicWithPlays,
    BoardgameUpdate,
)
from sabogaapi.api_v1.users import RoleChecker, current_active_user

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgamePublicWithPlays])
async def read_all_games() -> List[Boardgame]:
    games = await Boardgame.find_all(fetch_links=True).to_list()
    return games


@router.post("/", response_model=BoardgamePublic)
async def add_boardgame(
    boardgame: BoardgameCreate, user: User = Depends(current_active_user)
) -> Boardgame:
    boardgame_response: Boardgame = await Boardgame.model_validate(
        boardgame, from_attributes=True
    ).create()
    return boardgame_response


@router.get("/{game_id}", response_model=BoardgamePublicWithPlays)
async def read_game(game_id: PydanticObjectId) -> Boardgame:
    game = await Boardgame.get(game_id, fetch_links=True)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.delete(
    "/{game_id}",
    dependencies=[Depends(RoleChecker(["staff", "admin"]))],
)
async def delete_game(game_id: PydanticObjectId) -> dict[str, bool]:
    game = await Boardgame.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await game.delete(link_rule=DeleteRules.DO_NOTHING)
    return {"ok": True}


@router.patch(
    "/{game_id}",
    dependencies=[Depends(RoleChecker(["staff", "admin"]))],
    response_model=BoardgamePublic,
)
async def update_game(game_id: PydanticObjectId, game: BoardgameUpdate) -> Boardgame:
    db_game = await Boardgame.get(game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    game_data = game.model_dump(exclude_unset=True)
    for key, value in game_data.items():
        setattr(db_game, key, value)
    await db_game.save()
    return db_game
