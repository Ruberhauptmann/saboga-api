import datetime
from collections.abc import Iterable
from typing import Any

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql import Subquery

from sabogaapi import models, schemas
from sabogaapi.database import AsyncSession
from sabogaapi.logger import configure_logger
from sabogaapi.services.base_entity_service import BaseEntityService

logger = configure_logger()


def latest_rank_subquery(compare_to: datetime.datetime) -> Subquery:
    rank_history_alias = aliased(models.RankHistory)

    return (
        select(
            rank_history_alias.boardgame_id,
            func.max(rank_history_alias.date).label("latest_date"),
        )
        .where(rank_history_alias.date < compare_to)
        .group_by(rank_history_alias.boardgame_id)
        .subquery()
    )


def joined_rank_history_subquery(compare_to: datetime.datetime) -> Subquery:
    latest_rank = latest_rank_subquery(compare_to)

    return (
        select(
            models.RankHistory.boardgame_id,
            models.RankHistory.bgg_rank.label("old_rank"),
            models.RankHistory.bgg_geek_rating.label("old_geek_rating"),
            models.RankHistory.bgg_average_rating.label("old_avg_rating"),
        )
        .join(
            latest_rank,
            and_(
                models.RankHistory.boardgame_id == latest_rank.c.boardgame_id,
                models.RankHistory.date == latest_rank.c.latest_date,
            ),
        )
        .subquery()
    )


class BoardgameService(
    BaseEntityService[
        models.Boardgame,
        schemas.BoardgameInList,
        schemas.BoardgameSingle,
        models.BoardgameNetwork,
    ]
):
    model = models.Boardgame
    schema = schemas.BoardgameInList
    schema_with_games = schemas.BoardgameSingle
    network_model = models.BoardgameNetwork

    @classmethod
    def _rows_to_boardgame_schemas(
        cls, rows: Iterable[Any]
    ) -> list[schemas.BoardgameInList]:
        games = []
        for row in rows:
            game: models.Boardgame = row[0]
            games.append(
                cls.schema(
                    **game.__dict__,
                    bgg_rank_change=row.bgg_rank_change,
                    bgg_average_rating_change=row.bgg_average_rating_change,
                    bgg_geek_rating_change=row.bgg_geek_rating_change,
                )
            )
        return games

    @staticmethod
    async def get_top_ranked_boardgames(
        db_session: AsyncSession,
        compare_to: datetime.datetime,
        page: int = 1,
        page_size: int = 50,
    ) -> list[schemas.BoardgameInList]:
        logger.debug(
            "Fetching top ranked boardgames (SQLAlchemy)",
            extra={
                "compare_to": compare_to.isoformat(),
                "page": page,
                "page_size": page_size,
            },
        )

        rank_alias = aliased(models.RankHistory)
        subq = (
            select(
                rank_alias.boardgame_id, func.max(rank_alias.date).label("latest_date")
            )
            .where(rank_alias.date < compare_to + datetime.timedelta(days=1))
            .group_by(rank_alias.boardgame_id)
            .cte("latest_rank_per_game")
        )

        latest_ranks = (
            select(rank_alias)
            .join(
                subq,
                and_(
                    rank_alias.boardgame_id == subq.c.boardgame_id,
                    rank_alias.date == subq.c.latest_date,
                ),
            )
            .subquery()
        )

        query = (
            select(
                models.Boardgame,
                (latest_ranks.c.bgg_rank - models.Boardgame.bgg_rank).label(
                    "bgg_rank_change"
                ),
                (
                    models.Boardgame.bgg_geek_rating - latest_ranks.c.bgg_geek_rating
                ).label("bgg_geek_rating_change"),
                (
                    models.Boardgame.bgg_average_rating
                    - latest_ranks.c.bgg_average_rating
                ).label("bgg_average_rating_change"),
            )
            .outerjoin(latest_ranks, models.Boardgame.id == latest_ranks.c.boardgame_id)
            .order_by(models.Boardgame.bgg_rank.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db_session.execute(query)
        rows = result.all()

        logger.info(
            "Top ranked boardgames fetched",
            extra={"returned_count": len(rows), "page": page, "page_size": page_size},
        )

        return BoardgameService._rows_to_boardgame_schemas(rows)

    @staticmethod
    async def get_boardgame_with_historical_data(
        db_session: AsyncSession,
        bgg_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        mode: str,
    ) -> schemas.BoardgameSingle | None:
        """Fetch a boardgame and its rank history in the given time range."""
        date_diff = (end_date - start_date).days
        if mode == "auto":
            if date_diff <= 30:
                mode = "daily"
            elif date_diff <= 180:
                mode = "weekly"
            else:
                mode = "yearly"

        # --- Get boardgame with relationships ---
        result = await db_session.execute(
            select(models.Boardgame)
            .options(
                selectinload(models.Boardgame.categories),
                selectinload(models.Boardgame.designers),
                selectinload(models.Boardgame.families),
                selectinload(models.Boardgame.mechanics),
            )
            .where(models.Boardgame.bgg_id == bgg_id)
        )
        boardgame = result.scalars().first()
        if not boardgame:
            return None

        # --- Rank history query ---
        rank_result = await db_session.execute(
            select(models.RankHistory)
            .where(
                models.RankHistory.boardgame_id == boardgame.id,
                models.RankHistory.date >= start_date,
                models.RankHistory.date <= end_date,
            )
            .order_by(models.RankHistory.date)
        )
        history = rank_result.scalars().all()

        # --- Downsampling by mode ---
        if mode == "weekly":
            history = history[::7]
        elif mode == "yearly":
            seen_years = set()
            yearly_history = []
            for rh in reversed(history):
                year = rh.date.year
                if year not in seen_years:
                    yearly_history.append(rh)
                    seen_years.add(year)
            history = list(reversed(yearly_history))

        latest_entry = history[-1] if history else None
        bgg_rank = latest_entry.bgg_rank if latest_entry else -1

        schema = schemas.BoardgameSingle.model_validate(boardgame)
        schema.bgg_rank = bgg_rank if bgg_rank else -1
        schema.bgg_rank_history = [
            schemas.RankHistory.model_validate(rh) for rh in history
        ]

        return schema

    @staticmethod
    async def get_trending_games(
        db_session: AsyncSession,
        limit: int = 5,
    ) -> list[schemas.BoardgameInList]:
        """Get trending games (biggest positive trend in last 30 days)."""
        compare_to = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
            days=30
        )

        rank_history_join = joined_rank_history_subquery(compare_to)

        query = (
            select(
                models.Boardgame,
                (rank_history_join.c.old_rank - models.Boardgame.bgg_rank).label(
                    "bgg_rank_change"
                ),
                (
                    models.Boardgame.bgg_average_rating
                    - rank_history_join.c.old_avg_rating
                ).label("bgg_average_rating_change"),
                (
                    models.Boardgame.bgg_geek_rating
                    - rank_history_join.c.old_geek_rating
                ).label("bgg_geek_rating_change"),
            )
            .outerjoin(
                rank_history_join,
                rank_history_join.c.boardgame_id == models.Boardgame.id,
            )
            .order_by(desc(models.Boardgame.mean_trend))
            .limit(limit)
        )

        result = await db_session.execute(query)
        return BoardgameService._rows_to_boardgame_schemas(result.all())

    @staticmethod
    async def get_declining_games(
        db_session: AsyncSession,
        limit: int = 5,
    ) -> list[schemas.BoardgameInList]:
        """Get declining games (biggest negative trend in last 30 days)."""
        compare_to = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
            days=30
        )

        rank_history_join = joined_rank_history_subquery(compare_to)

        query = (
            select(
                models.Boardgame,
                (rank_history_join.c.old_rank - models.Boardgame.bgg_rank).label(
                    "bgg_rank_change"
                ),
                (
                    models.Boardgame.bgg_average_rating
                    - rank_history_join.c.old_avg_rating
                ).label("bgg_average_rating_change"),
                (
                    models.Boardgame.bgg_geek_rating
                    - rank_history_join.c.old_geek_rating
                ).label("bgg_geek_rating_change"),
            )
            .outerjoin(
                rank_history_join,
                rank_history_join.c.boardgame_id == models.Boardgame.id,
            )
            .order_by(asc(models.Boardgame.mean_trend))
            .limit(limit)
        )

        result = await db_session.execute(query)
        return BoardgameService._rows_to_boardgame_schemas(result.all())
