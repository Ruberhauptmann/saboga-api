"""Service layer for designer."""

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger
from sabogaapi.services.base_entity_service import BaseEntityService

logger = configure_logger()


class CategoryService(
    BaseEntityService[
        models.Category,
        schemas.Category,
        schemas.CategoryWithBoardgames,
        models.CategoryNetwork,
    ]
):
    model = models.Category
    schema = schemas.Category
    schema_with_games = schemas.CategoryWithBoardgames
    network_model = models.CategoryNetwork
