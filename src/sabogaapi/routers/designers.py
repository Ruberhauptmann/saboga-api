"""Routes for viewing the designers data."""

from fastapi import APIRouter

from sabogaapi.logger import configure_logger

logger = configure_logger()

router = APIRouter(
    prefix="/designers",
    tags=["Designers"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_designers() -> dict[str, str]:
    return {"status": "not yet implemented"}
