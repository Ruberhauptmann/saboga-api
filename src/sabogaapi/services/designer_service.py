"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.services.base_entity_service import BaseEntityService

logger = configure_logger()


class DesignerService(
    BaseEntityService[
        models.Designer,
        schemas.Designer,
        schemas.DesignerWithBoardgames,
        models.DesignerNetwork,
    ]
):
    model = models.Designer
    schema = schemas.Designer
    schema_with_games = schemas.DesignerWithBoardgames
    network_model = models.DesignerNetwork
