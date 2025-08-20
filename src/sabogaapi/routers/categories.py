"""Routes for viewing the category data."""

from fastapi import APIRouter, HTTPException

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Category
from sabogaapi.services.category_service import CategoryService

logger = configure_logger()

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_all_categories() -> list[Category]:
    return await CategoryService.read_all_categories()


@router.get("/{bgg_id}")
async def read_category(bgg_id: int) -> Category:
    category = await CategoryService.read_category(bgg_id=bgg_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
