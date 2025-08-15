"""Routes for viewing the mechanics data."""

from fastapi import APIRouter

from sabogaapi.logger import configure_logger

logger = configure_logger()

router = APIRouter(
    prefix="/mechanics",
    tags=["Mechanics"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_mechanics() -> dict[str, str]:
    return {"status": "not yet implemented"}
