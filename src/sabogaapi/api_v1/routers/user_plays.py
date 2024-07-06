from typing import List, Sequence

from beanie import DeleteRules, PydanticObjectId, WriteRules
from fastapi import APIRouter, Depends, HTTPException

from sabogaapi.api_v1.models import Boardgame, Play, Result, User
from sabogaapi.api_v1.schemas import (
    PlayCreate,
    PlayPublic,
    PlayUpdate,
    ResultCreate,
    ResultPublic,
)
from sabogaapi.api_v1.users import current_active_user

router = APIRouter(
    prefix="/{user_id}/plays",
    tags=["User Ressources"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[PlayPublic])
async def read_all_plays(user: User = Depends(current_active_user)) -> Sequence[Play]:
    plays = await Play.find(Play.user.id == user.id, fetch_links=True).to_list()
    if not plays:
        raise HTTPException(status_code=404, detail="No plays in database")
    return plays


@router.post("/", response_model=PlayPublic)
async def create_play(
    play: PlayCreate, user: User = Depends(current_active_user)
) -> Play:
    play_response: Play = await Play.model_validate(play, from_attributes=True).create()
    play_response.user = user
    await play_response.save(link_rule=WriteRules.WRITE)
    return play_response


@router.post("/{play_id}/results", response_model=ResultPublic)
async def create_result(
    play_id: PydanticObjectId,
    result: ResultCreate,
    user: User = Depends(current_active_user),
) -> Result:
    result_response: Result = await Result.model_validate(
        result, from_attributes=True
    ).create()
    play = await Play.get(play_id, fetch_links=True)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    play.results.append(result_response)
    await play.save(link_rule=WriteRules.WRITE)
    return result_response


@router.get("/{play_id}", response_model=PlayPublic)
async def read_play(
    play_id: PydanticObjectId, user: User = Depends(current_active_user)
) -> Play:
    play = await Play.get(play_id, fetch_links=True)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    if not play.user == user:
        raise HTTPException(
            status_code=401, detail="This play does not belong to this user"
        )
    return play


@router.delete("/{play_id}")
async def delete_play(
    play_id: PydanticObjectId, user: User = Depends(current_active_user)
) -> dict[str, bool]:
    play = await Play.get(play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    if not play.user == user:
        raise HTTPException(
            status_code=401, detail="This play does not belong to this user"
        )
    await play.delete(link_rule=DeleteRules.DELETE_LINKS)
    return {"ok": True}


@router.patch("/{play_id}", response_model=PlayPublic)
async def update_play(
    play_id: PydanticObjectId,
    play: PlayUpdate,
    user: User = Depends(current_active_user),
) -> Play:
    db_play = await Play.get(play_id, fetch_links=True)
    if not db_play:
        raise HTTPException(status_code=404, detail="Play not found")
    if not db_play.user == user:
        raise HTTPException(
            status_code=401, detail="This play does not belong to this user"
        )
    play_data = play.model_dump(exclude_unset=True)
    for key, value in play_data.items():
        setattr(db_play, key, value)
    await db_play.save()
    return db_play


@router.put("/{play_id}/games/{game_id}/", response_model=PlayPublic)
async def add_play_to_boardgame(
    game_id: PydanticObjectId,
    play_id: PydanticObjectId,
    user: User = Depends(current_active_user),
) -> Play:
    game = await Boardgame.get(game_id, fetch_links=True)
    play = await Play.get(play_id, fetch_links=True)
    if not play:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game:
        raise HTTPException(status_code=404, detail="Play not found")
    if not play.user == user:
        raise HTTPException(
            status_code=401, detail="This play does not belong to this user"
        )

    play.games_played.append(game)
    await play.save(link_rule=WriteRules.WRITE)
    return play
