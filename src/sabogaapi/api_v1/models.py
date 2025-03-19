"""Beanie database models."""

import datetime
from typing import Annotated, List, Optional

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


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed(unique=True)]
    name: str
    last_data_sync: Optional[datetime.datetime] = None
    bgg_rank_history: List["RankHistory"] = []

    @staticmethod
    async def get_top_ranked_boardgames(
        date: datetime.datetime,
        compare_to: datetime.datetime,
        page: int = 1,
        page_size: int = 10,
    ) -> List[BoardgameHistoricalData]:
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
                                    "cond": {"$lte": ["$$history.date", compare_to]},
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
                                    "$previous_rank_data.bgg_rank",
                                    "$current_rank_data.bgg_rank",
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


class RankHistory(BaseModel):
    date: datetime.datetime
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None
