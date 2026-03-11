from fastapi import APIRouter

from sabogaapi.api.dependencies.core import DBSessionDep
from sabogaapi.schemas import SearchResult
from sabogaapi.services import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def search(
    db_session: DBSessionDep, query: str, limit: int = 10
) -> list[SearchResult]:
    return await SearchService.search(db_session=db_session, query=query, limit=limit)
