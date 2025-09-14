"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class FamilyService:
    """Service layer for mechanics."""

    @staticmethod
    async def get_total_count() -> int:
        """Get number of families.

        Returns:
            int: Number of families.

        """
        return await models.Family.find_all().count()

    @staticmethod
    async def read_all_families(
        page: int,
        per_page: int,
    ) -> list[schemas.Family]:
        family_list = (
            await models.Family.find()
            .sort("+name")
            .skip((page - 1) * per_page)
            .limit(per_page)
            .to_list()
        )
        return [schemas.Family(**family.model_dump()) for family in family_list]

    @staticmethod
    async def read_family(bgg_id: int) -> schemas.FamilyWithBoardgames | None:
        family = await models.Family.find(
            models.Family.bgg_id == bgg_id, fetch_links=True
        ).first_or_none()
        if family is None:
            return None

        return schemas.FamilyWithBoardgames(**family.model_dump())

    @staticmethod
    async def get_family_network() -> schemas.Network:
        network = await models.FamilyNetwork.find().first_or_none()

        if network is None:
            return schemas.Network(nodes=[], edges=[])

        return schemas.Network(**network.model_dump())
