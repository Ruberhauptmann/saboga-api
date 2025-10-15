"""Service layer for rank history (PostgreSQL / SQLAlchemy)."""

import datetime

from sqlalchemy import select

from sabogaapi import models, schemas
from sabogaapi.api.dependencies.core import DBSessionDep
from sabogaapi.logger import configure_logger

logger = configure_logger()


class RankHistoryService:
    """Service layer for rank history."""

    @staticmethod
    async def get_rank_history_before_date(
        db_session: DBSessionDep, bgg_id: int, end_date: datetime.date
    ) -> list[schemas.RankHistory]:
        """Get rank history entries before a certain date.

        Args:
            bgg_id (int): ID for boardgame.
            end_date (datetime.date): Last date.

        Returns:
            List[schemas.RankHistory]: List of rank history elements.
        """
        result = await db_session.execute(
            select(models.RankHistory)
            .where(
                models.RankHistory.bgg_id == bgg_id,
                models.RankHistory.date < end_date,
            )
            .order_by(models.RankHistory.date.asc())
        )
        rank_history_rows = result.scalars().all()

        return [schemas.RankHistory.from_orm(row) for row in rank_history_rows]
