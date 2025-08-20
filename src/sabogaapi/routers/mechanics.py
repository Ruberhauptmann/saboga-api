"""Routes for viewing the mechanics data."""

from fastapi import APIRouter, HTTPException

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Mechanic
from sabogaapi.services.mechanic_service import MechanicService

logger = configure_logger()

router = APIRouter(
    prefix="/mechanics",
    tags=["Mechanics"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_mechanics() -> list[Mechanic]:
    return await MechanicService.read_all_mechanics()


@router.get("/{bgg_id}")
async def read_mechanic(bgg_id: int) -> Mechanic:
    mechanic = await MechanicService.read_mechanic(bgg_id=bgg_id)
    if not mechanic:
        raise HTTPException(status_code=404, detail="Mechanic not found")
    return mechanic
