"""Routes for viewing the designers data."""

from typing import Any

from fastapi import APIRouter

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Designer
from sabogaapi.services import DesignerService

logger = configure_logger()

router = APIRouter(
    prefix="/designers",
    tags=["Designers"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_designers() -> list[Designer]:
    return await DesignerService.read_all_designers()


@router.get("/clusters")
async def read_designer_clusters() -> dict[str, list[dict[str, Any]]]:
    return await DesignerService.get_designer_network()
