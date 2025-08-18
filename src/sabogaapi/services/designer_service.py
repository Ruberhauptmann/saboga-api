"""Service layer for designer."""


from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class DesignerService:
    """Service layer for designer."""

    @staticmethod
    async def read_all_designers() -> list[schemas.Designer]:
        """Read all designers.

        Returns:
            list[schemas.Designer]: List of designers.

        """
        designer_list = await models.Designer.find().to_list()
        return [schemas.Designer(**designer.model_dump()) for designer in designer_list]

    @staticmethod
    async def get_designer_network() -> schemas.DesignerNetwork:
        network = await models.DesignerNetwork.find().first_or_none()

        if network is None:
            return schemas.DesignerNetwork(nodes=[], edges=[])

        return schemas.DesignerNetwork(**network.model_dump())
