from typing import List, Sequence

from beanie import DeleteRules, PydanticObjectId, WriteRules
from fastapi import APIRouter, Depends, HTTPException

from sabogaapi.api_v1.models import Boardgame, Collection, User
from sabogaapi.api_v1.schemas import (
    BoardgamePublic,
    CollectionCreate,
    CollectionPublic,
    CollectionUpdate,
    PlayCreate,
    PlayPublic,
    PlayUpdate,
)
from sabogaapi.api_v1.users import current_active_user

router = APIRouter(
    prefix="/{id}/collections",
    tags=["User Ressources"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[CollectionPublic])
async def read_all_collections(
    user: User = Depends(current_active_user),
) -> Sequence[Collection]:
    collections = await Collection.find(
        Collection.user.id == user.id, fetch_links=True
    ).to_list()
    if not collections:
        raise HTTPException(
            status_code=404, detail="No collections for user in database"
        )
    return collections


@router.post("/", response_model=CollectionPublic)
async def create_collection(
    collection: CollectionCreate, user: User = Depends(current_active_user)
) -> Collection:
    collection_response: Collection = Collection.model_validate(
        collection, from_attributes=True
    )
    collection_response.user = user
    await collection_response.save(link_rule=WriteRules.WRITE)
    return collection_response


@router.put("/{collection_id}/games/{game_id}/", response_model=CollectionPublic)
async def add_game_to_collection(
    game_id: PydanticObjectId,
    collection_id: PydanticObjectId,
    user: User = Depends(current_active_user),
) -> Collection:
    game = await Boardgame.get(game_id, fetch_links=True)
    collection = await Collection.get(collection_id, fetch_links=True)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not collection.user == user:
        raise HTTPException(
            status_code=401, detail="This collection does not belong to this user"
        )
    collection.games.append(game)
    await collection.save(link_rule=WriteRules.WRITE)
    return collection


@router.get("/{collection_id}", response_model=CollectionPublic)
async def read_collection(
    collection_id: PydanticObjectId, user: User = Depends(current_active_user)
) -> Collection:
    collection = await Collection.get(collection_id, fetch_links=True)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not collection.user == user:
        raise HTTPException(
            status_code=401, detail="This collection does not belong to this user"
        )
    return collection


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: PydanticObjectId, user: User = Depends(current_active_user)
) -> dict[str, bool]:
    collection = await Collection.get(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not collection.user == user:
        raise HTTPException(
            status_code=401, detail="This collection does not belong to this user"
        )
    await collection.delete(link_rule=DeleteRules.DELETE_LINKS)
    return {"ok": True}


@router.patch("/{collection_id}", response_model=CollectionPublic)
async def update_collection(
    collection_id: PydanticObjectId,
    collection: CollectionUpdate,
    user: User = Depends(current_active_user),
) -> Collection:
    db_collection = await Collection.get(collection_id, fetch_links=True)
    if not db_collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not db_collection.user == user:
        raise HTTPException(
            status_code=401, detail="This collection does not belong to this user"
        )
    collection_data = collection.model_dump(exclude_unset=True)
    for key, value in collection_data.items():
        setattr(db_collection, key, value)
    await db_collection.save()
    return db_collection
