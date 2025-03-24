from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from sabogaapi.api_v1.models import Boardgame

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


class SearchResult(BaseModel):
    bgg_id: int
    name: str


@router.get("", response_model=List[SearchResult])
async def search(query: str, limit: int = 10) -> List[SearchResult]:
    results = (
        await Boardgame.find({"name": {"$regex": query, "$options": "i"}})
        .project(SearchResult)
        .limit(limit)
        .to_list()
    )

    return results
