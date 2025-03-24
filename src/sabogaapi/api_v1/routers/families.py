"""Routes for viewing the families data."""

from fastapi import APIRouter

from sabogaapi.logger import configure_logger

logger = configure_logger()

router = APIRouter(
    prefix="/families",
    tags=["Families"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_all_families() -> dict[str, str]:
    return {"status": "not yet implemented"}
