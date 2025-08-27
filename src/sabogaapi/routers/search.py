from fastapi import APIRouter

from sabogaapi.schemas import SearchResult
from sabogaapi.services import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def search(query: str, limit: int = 10) -> list[SearchResult]:
    return await SearchService.search(query=query, limit=limit)
