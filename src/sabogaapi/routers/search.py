from fastapi import APIRouter

from sabogaapi.schemas import SearchResult
from sabogaapi.services import BoardgameService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=list[SearchResult])
async def search(query: str, limit: int = 10) -> list[SearchResult]:
    results = await BoardgameService.search(query=query, limit=limit)
    return results
