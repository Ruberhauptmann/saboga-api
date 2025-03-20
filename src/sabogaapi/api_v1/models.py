"""Beanie database models."""

import datetime
from typing import Annotated, List, Optional

from beanie import Document, Indexed
from pydantic import BaseModel


class BoardgameComparison(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int
    bgg_rank_change: int
    bgg_geek_rating: float
    bgg_geek_rating_change: float
    bgg_average_rating: float
    bgg_average_rating_change: float


class BoardgameWithHistoricalData(BaseModel):
    bgg_id: int
    name: str
    bgg_rank: int
    bgg_geek_rating: float
    bgg_average_rating: float
    bgg_rank_history: List["RankHistory"]


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
    ) -> List[BoardgameComparison]:
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
            aggregation_pipeline=pipeline, projection_model=BoardgameComparison
        ).to_list()

        return rank_data

    @staticmethod
    async def get_boardgame_with_historical_data(
        bgg_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        mode: str,
    ) -> BoardgameWithHistoricalData | None:
        # Determine dynamic granularity if "auto" is selected
        date_diff = (end_date - start_date).days
        if mode == "auto":
            if date_diff <= 30:
                mode = "daily"
            elif date_diff <= 180:
                mode = "weekly"
            else:
                mode = "yearly"

        pipeline = [
            {"$match": {"bgg_id": bgg_id}},  # Match board game by ID
            {"$unwind": "$bgg_rank_history"},  # Unwind the bgg_rank_history array
            {
                "$match": {  # Filter rank history by date range
                    "bgg_rank_history.date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {"$sort": {"bgg_rank_history.date": 1}},  # Sort by date (ascending)
            {
                "$group": {
                    "_id": "$bgg_id",
                    "name": {"$first": "$name"},
                    "bgg_rank_history": {
                        "$push": "$bgg_rank_history"
                    },  # Push all rank history entries
                    "latest_rank": {
                        "$last": "$bgg_rank_history"
                    },  # Get the last entry in the array (latest rank)
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "bgg_id": "$_id",
                    "name": 1,
                    "bgg_rank": "$latest_rank.bgg_rank",
                    "bgg_geek_rating": "$latest_rank.bgg_geek_rating",
                    "bgg_average_rating": "$latest_rank.bgg_average_rating",
                    "bgg_rank_history": 1,
                }
            },
        ]

        result = await Boardgame.aggregate(
            aggregation_pipeline=pipeline, projection_model=BoardgameWithHistoricalData
        ).to_list()

        if not result:
            return None

        boardgame_data = result[0]

        # Apply mode filtering to bgg_rank_history in Python
        history = boardgame_data.bgg_rank_history

        if mode == "weekly":
            history = history[::7]  # Every 7th entry
        elif mode == "yearly":
            seen_years = set()
            yearly_history = []
            for entry in history:
                year = entry["date"].year
                if year not in seen_years:
                    yearly_history.append(entry)
                    seen_years.add(year)
            history = yearly_history

        boardgame_data.bgg_rank_history = history
        return boardgame_data

    class Settings:
        name = "boardgames"


class RankHistory(BaseModel):
    date: datetime.datetime
    bgg_rank: int | None
    bgg_geek_rating: float | None
    bgg_average_rating: float | None
