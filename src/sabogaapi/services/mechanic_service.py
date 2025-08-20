"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class MechanicService:
    """Service layer for mechanics."""

    @staticmethod
    async def read_all_mechanics() -> list[schemas.Mechanic]:
        mechanic_list = await models.Mechanic.find().to_list()
        return [schemas.Mechanic(**mechanic.model_dump()) for mechanic in mechanic_list]

    @staticmethod
    async def read_mechanic(bgg_id: int) -> schemas.Mechanic | None:
        mechanic = await models.Mechanic.find(
            models.Mechanic.bgg_id == bgg_id
        ).first_or_none()
        if mechanic is None:
            return None
        return schemas.Mechanic(**mechanic.model_dump())
