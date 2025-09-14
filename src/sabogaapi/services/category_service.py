"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class CategoryService:
    """Service layer for category."""

    @staticmethod
    async def get_total_count() -> int:
        """Get number of category.

        Returns:
            int: Number of categories.

        """
        return await models.Category.find_all().count()

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
    async def read_category(bgg_id: int) -> schemas.CategoryWithBoardgames | None:
        category = await models.Category.find(
            models.Category.bgg_id == bgg_id, fetch_links=True
        ).first_or_none()
        if category is None:
            return None
        return schemas.CategoryWithBoardgames(**category.model_dump())

    @staticmethod
    async def get_category_network() -> schemas.Network:
        network = await models.CategoryNetwork.find().first_or_none()

        if network is None:
            return schemas.Network(nodes=[], edges=[])

        return schemas.Network(**network.model_dump())
