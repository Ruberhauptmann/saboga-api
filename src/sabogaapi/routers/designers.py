"""Routes for viewing the designers data."""

from fastapi import APIRouter

from sabogaapi.logger import configure_logger
from sabogaapi.models import Boardgame

logger = configure_logger()

router = APIRouter(
    prefix="/designers",
    tags=["Designers"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_designers() -> list[Boardgame]:
    designer_list = await Boardgame.get_designers()
    return designer_list


@router.get("/clusters")
async def read_designer_clusters() -> dict[str, str]:
    return {"status": "not yet implemented"}
