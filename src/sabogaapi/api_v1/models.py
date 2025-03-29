"""Beanie database models."""

import datetime
from typing import Annotated, Any, List

from beanie import Document, Indexed, TimeSeriesConfig
from pydantic import BaseModel, Field


class BoardgameWithHistoricalData(BaseModel):
    bgg_id: int
    name: str = ""
    description: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_published: int | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    categories: List["Category"] = []
    families: List["Family"] = []
    designers: List["Designer"] = []
    mechanics: List["Mechanic"] = []
    bgg_rank: int
    bgg_geek_rating: float
    bgg_average_rating: float
    bgg_rank_history: List["RankHistorySingleGame"]


class RankHistory(Document):
    date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    bgg_id: int
    bgg_rank: int | None = None
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None

    class Settings:
        timeseries = TimeSeriesConfig(
            time_field="date",
            meta_field="bgg_id",
            bucketRoundingSeconds=86400,
            bucketMaxSpanSeconds=86400,
        )
        name = "rank_history"


class RankHistorySingleGame(BaseModel):
    date: datetime.datetime
    bgg_rank: int | None = None
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None


class Category(BaseModel):
    name: str
    bgg_id: int


class Family(BaseModel):
    name: str
    bgg_id: int


class Mechanic(BaseModel):
    name: str
    bgg_id: int


class Designer(BaseModel):
    name: str
    bgg_id: int


class Boardgame(Document):
    bgg_id: Annotated[int, Indexed(unique=True)]
    name: str = ""
    bgg_rank: int | None = None
    bgg_geek_rating: float | None = None
    bgg_average_rating: float | None = None
    description: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    year_published: int | None = None
    minplayers: int | None = None
    maxplayers: int | None = None
    playingtime: int | None = None
    minplaytime: int | None = None
    maxplaytime: int | None = None
    categories: List[Category] = []
    families: List["Family"] = []
    mechanics: List[Mechanic] = []
    designers: List[Designer] = []

    @staticmethod
    async def get_top_ranked_boardgames(
        compare_to: datetime.datetime,
        page: int = 1,
        page_size: int = 100,
    ) -> List[dict[str, Any]]:
        find_rank_comparison = [
            {"$addFields": {"sortrank": {"$ifNull": ["$bgg_rank", True]}}},
            {"$sort": {"sortrank": 1}},
            {"$skip": page * page_size},
            {"$limit": page_size},
            {
                "$lookup": {
                    "from": f"{RankHistory.Settings.name}",
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$bgg_id", "$$bgg_id"]},
                                "date": {"$lte": compare_to},
                            }
                        },
                        {"$sort": {"date": -1}},
                        {"$limit": 1},
                    ],
                    "as": "rank_history",
                }
            },
            {"$set": {"rank_history": {"$arrayElemAt": ["$rank_history", 0]}}},
            {
                "$set": {
                    "bgg_rank_change": {
                        "$subtract": ["$bgg_rank", "$rank_history.bgg_rank"]
                    },
                    "bgg_average_rating_change": {
                        "$subtract": [
                            "$bgg_average_rating",
                            "$rank_history.bgg_average_rating",
                        ]
                    },
                    "bgg_geek_rating_change": {
                        "$subtract": [
                            "$bgg_geek_rating",
                            "$rank_history.bgg_geek_rating",
                        ]
                    },
                }
            },
        ]

        rank_data = await Boardgame.aggregate(
            aggregation_pipeline=find_rank_comparison
        ).to_list()
        print(rank_data)

        return rank_data

    @staticmethod
    async def get_boardgame_with_historical_data(
        bgg_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        mode: str,
    ) -> BoardgameWithHistoricalData | None:
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
                    "latest_rank": {
                        "$last": "$bgg_rank_history"
                    },  # Get latest rank entry
                    "bgg_rank_history": {
                        "$push": "$bgg_rank_history"
                    },  # Keep all history
                    "doc": {"$first": "$$ROOT"},  # Store the full document
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "bgg_id": "$_id",
                    "bgg_rank": "$latest_rank.bgg_rank",
                    "bgg_geek_rating": "$latest_rank.bgg_geek_rating",
                    "bgg_average_rating": "$latest_rank.bgg_average_rating",
                    "doc": 1,  # Keep full document data
                    "bgg_rank_history": 1,
                }
            },
            {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", "$$ROOT"]}}},
        ]

        result = await Boardgame.aggregate(
            aggregation_pipeline=pipeline, projection_model=BoardgameWithHistoricalData
        ).to_list()

        if not result:
            return None

        boardgame_data = result[0]

        # Apply mode filtering to bgg_rank_history
        history = boardgame_data.bgg_rank_history
        if mode == "weekly":
            history = history[::7]  # Every 7th entry
        elif mode == "yearly":
            seen_years = set()
            yearly_history = []
            for entry in history:
                year = entry.date.year
                if year not in seen_years:
                    yearly_history.append(entry)
                    seen_years.add(year)
            history = yearly_history

        boardgame_data.bgg_rank_history = history
        return boardgame_data

    class Settings:
        name = "boardgames"
