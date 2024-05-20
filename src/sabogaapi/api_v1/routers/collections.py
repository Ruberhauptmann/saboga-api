from typing import List, Sequence

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from sabogaapi.api_v1.models import Collection
from sabogaapi.api_v1.schemas import CollectionPublic

router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[CollectionPublic])
async def read_all_collections() -> Sequence[Collection]:
    collections = await Collection.find_all(fetch_links=True).to_list()
    if not collections:
        raise HTTPException(status_code=404, detail="No plays in database")
    return collections


@router.get("/{collection_id}", response_model=CollectionPublic)
async def read_collection(collection_id: PydanticObjectId) -> Collection:
    collection = await Collection.get(collection_id, fetch_links=True)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection
