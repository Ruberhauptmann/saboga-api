"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.services.base_entity_service import BaseEntityService

logger = configure_logger()


class FamilyService(
    BaseEntityService[
        models.Family,
        schemas.Family,
        schemas.FamilyWithBoardgames,
        models.FamilyNetwork,
    ]
):
    model = models.Family
    schema = schemas.Family
    schema_with_games = schemas.FamilyWithBoardgames
    network_model = models.FamilyNetwork
