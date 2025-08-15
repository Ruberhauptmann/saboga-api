from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class DesignerService:
    @staticmethod
    async def read_all_designers() -> list[schemas.Designer]:
        designer_list = await models.Designer.find().to_list()
        return [schemas.Designer(**designer.model_dump()) for designer in designer_list]
