"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class CategoryService:
    """Service layer for category."""

    @staticmethod
    async def read_all_categories(
        page: int = 1,
        page_size: int = 50,
    ) -> list[schemas.Category]:
        category_list = (
            await models.Category.find()
            .sort("name")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return [schemas.Category(**category.model_dump()) for category in category_list]

    @staticmethod
    async def read_category(bgg_id: int) -> schemas.Category | None:
        category = await models.Category.find(
            models.Category.bgg_id == bgg_id
        ).first_or_none()
        if category is None:
            return None
        return schemas.Category(**category.model_dump())
