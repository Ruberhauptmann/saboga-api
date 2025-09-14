"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class MechanicService:
    """Service layer for mechanics."""

    @staticmethod
    async def get_total_count() -> int:
        """Get number of mechanics.

        Returns:
            int: Number of mechanics.

        """
        return await models.Mechanic.find_all().count()

    @staticmethod
    async def read_all_mechanics(
        page: int,
        per_page: int,
    ) -> list[schemas.Mechanic]:
        mechanic_list = (
            await models.Mechanic.find()
            .sort("+name")
            .skip((page - 1) * per_page)
            .limit(per_page)
            .to_list()
        )
        return [schemas.Mechanic(**mechanic.model_dump()) for mechanic in mechanic_list]

    @staticmethod
    async def read_mechanic(bgg_id: int) -> schemas.MechanicWithBoardgames | None:
        mechanic = await models.Mechanic.find(
            models.Mechanic.bgg_id == bgg_id, fetch_links=True
        ).first_or_none()
        if mechanic is None:
            return None
        return schemas.MechanicWithBoardgames(**mechanic.model_dump())

    @staticmethod
    async def get_mechanic_network() -> schemas.Network:
        network = await models.MechanicNetwork.find().first_or_none()

        if network is None:
            return schemas.Network(nodes=[], edges=[])

        return schemas.Network(**network.model_dump())
