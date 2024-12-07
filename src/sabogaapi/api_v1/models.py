"""Beanie database models."""

from datetime import datetime, timedelta
from typing import Annotated, List, Optional, Tuple

from beanie import Document, Indexed
from pydantic import BaseModel


class BoardgameHistoricalData(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int
    bgg_rank_change: int
    bgg_geek_rating: float
    bgg_geek_rating_change: float
    bgg_average_rating: float
    bgg_average_rating_change: float
    bgg_rank_history: List["RankHistory"] = []


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed(unique=True)]
    name: str
    last_data_sync: Optional[datetime] = None

    @staticmethod
    async def get_date_range_from_week_year(
        week_year: str, compare_to: str | None
    ) -> Tuple[datetime, datetime]:
        year, week = map(int, week_year.split("/"))
        date = datetime.fromisocalendar(year, week, 7)
        if compare_to is None:
            previous_date = date - timedelta(weeks=1)
        else:
            year, week = map(int, compare_to.split("/"))
            previous_date = datetime.fromisocalendar(year, week, 7)
        return date, previous_date

    @staticmethod
    async def get_top_ranked_boardgames(
        week_year: str, compare_to: str | None, page: int = 1, page_size: int = 10
    ) -> List[BoardgameHistoricalData]:
        date, date_previous = await Boardgame.get_date_range_from_week_year(
            week_year, compare_to
        )
        print(date, date_previous, flush=True)

        pipeline = [
            {
                "$addFields": {
                    "current_rank_data": {
                        "$arrayElemAt": [
                            {
                                "$filter": {
                                    "input": "$bgg_rank_history",
                                    "as": "history",
                                    "cond": {"$lte": ["$$history.date", date]},
                                }
                            },
                            -1,
                        ]
                    }
                }
            },
            {"$match": {"current_rank_data.bgg_rank": {"$ne": None}}},
            {"$sort": {"current_rank_data.bgg_rank": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
            {
                "$addFields": {
                    "previous_rank_data": {
                        "$arrayElemAt": [
                            {
                                "$filter": {
                                    "input": "$bgg_rank_history",
                                    "as": "history",
                                    "cond": {"$lte": ["$$history.date", date_previous]},
                                }
                            },
                            -1,
                        ]
                    },
                }
            },
            {
                "$addFields": {
                    "bgg_rank": "$current_rank_data.bgg_rank",
                    "bgg_rank_change": {
                        "$ifNull": [
                            {
                                "$subtract": [
                                    "$current_rank_data.bgg_rank",
                                    "$previous_rank_data.bgg_rank",
                                ]
                            },
                            0,
                        ]
                    },
                    "bgg_geek_rating": "$current_rank_data.bgg_geek_rating",
                    "bgg_geek_rating_change": {
                        "$ifNull": [
                            {
                                "$subtract": [
                                    "$current_rank_data.bgg_geek_rating",
                                    "$previous_rank_data.bgg_geek_rating",
                                ]
                            },
                            0,
                        ]
                    },
                    "bgg_average_rating": "$current_rank_data.bgg_average_rating",
                    "bgg_average_rating_change": {
                        "$ifNull": [
                            {
                                "$subtract": [
                                    "$current_rank_data.bgg_average_rating",
                                    "$previous_rank_data.bgg_average_rating",
                                ]
                            },
                            0,
                        ]
                    },
                }
            },
        ]

        rank_data = await Boardgame.aggregate(
            aggregation_pipeline=pipeline, projection_model=BoardgameHistoricalData
        ).to_list()

        return rank_data

    class Settings:
        name = "boardgames"


class BoardgameSettings(Document):
    last_bgg_scrape: datetime
    last_scraped_id: int

    class Settings:
        name = "boardgames.settings"


class RankHistory(BaseModel):
    date: datetime
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None
