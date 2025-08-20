"""Routes for viewing the families data."""

from fastapi import APIRouter, HTTPException

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Family
from sabogaapi.services.family_service import FamilyService

logger = configure_logger()

router = APIRouter(
    prefix="/families",
    tags=["Families"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_families() -> list[Family]:
    return await FamilyService.read_all_families()


@router.get("/{bgg_id}")
async def read_family(bgg_id: int) -> Family:
    family = await FamilyService.read_family(bgg_id=bgg_id)
    if not family:
        raise HTTPException(status_code=404, detail="Mechanic not found")
    return family
