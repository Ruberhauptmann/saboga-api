from typing import List, Sequence

from beanie import DeleteRules, PydanticObjectId
from fastapi import APIRouter, HTTPException

from sabogaapi.api_v1.models import Play
from sabogaapi.api_v1.schemas import PlayCreate, PlayPublicWithBoardgames, PlayUpdate

router = APIRouter(
    prefix="/plays",
    tags=["plays"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[PlayPublicWithBoardgames])
async def read_all_plays() -> Sequence[Play]:
    plays = await Play.find_all(fetch_links=True).to_list()
    return plays


@router.post("/", response_model=PlayPublicWithBoardgames)
async def create_play(play: PlayCreate) -> Play:
    play_response: Play = await Play.model_validate(play, from_attributes=True).create()
    return play_response


@router.get("/{play_id}", response_model=PlayPublicWithBoardgames)
async def read_play(play_id: PydanticObjectId) -> Play:
    play = await Play.get(play_id, fetch_links=True)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    return play


@router.delete("/{play_id}")
async def delete_play(play_id: PydanticObjectId) -> dict[str, bool]:
    play = await Play.get(play_id)
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    await play.delete(link_rule=DeleteRules.DELETE_LINKS)
    return {"ok": True}


@router.patch("/{play_id}", response_model=PlayPublicWithBoardgames)
async def update_play(play_id: int, play: PlayUpdate) -> Play:
    db_play = await Play.get(play_id, fetch_links=True)
    if not db_play:
        raise HTTPException(status_code=404, detail="Play not found")
    play_data = play.model_dump(exclude_unset=True)
    for key, value in play_data.items():
        setattr(db_play, key, value)
    await db_play.save()
    return db_play
