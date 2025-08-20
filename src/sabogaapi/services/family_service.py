"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class FamilyService:
    """Service layer for mechanics."""

    @staticmethod
    async def read_all_families() -> list[schemas.Family]:
        family_list = await models.Family.find().to_list()
        return [schemas.Family(**family.model_dump()) for family in family_list]

    @staticmethod
    async def read_family(bgg_id: int) -> schemas.Family | None:
        family = await models.Family.find(
            models.Family.bgg_id == bgg_id
        ).first_or_none()
        if family is None:
            return None
        return schemas.Family(**family.model_dump())
