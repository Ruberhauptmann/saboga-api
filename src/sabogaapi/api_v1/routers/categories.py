"""Routes for viewing the category data."""

from fastapi import APIRouter

from sabogaapi.logger import configure_logger

logger = configure_logger()

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_all_categories() -> dict[str, str]:
    return {"status": "not yet implemented"}
