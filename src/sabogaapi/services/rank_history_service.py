import datetime

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class RankHistoryService:
    @staticmethod
    async def get_rank_history_before_date(bgg_id: int, end_date: datetime.date):
        bgg_rank_history = await models.RankHistory.find(
            models.RankHistory.bgg_id == bgg_id, models.RankHistory.date < end_date
        ).to_list()
        return [
            schemas.RankHistory(**result.model_dump()) for result in bgg_rank_history
        ]
