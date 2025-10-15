"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.services.base_entity_service import BaseEntityService

logger = configure_logger()


class MechanicService(
    BaseEntityService[
        models.Mechanic,
        schemas.Mechanic,
        schemas.MechanicWithBoardgames,
        models.MechanicNetwork,
    ]
):
    model = models.Mechanic
    schema = schemas.Mechanic
    schema_with_games = schemas.MechanicWithBoardgames
    network_model = models.MechanicNetwork
