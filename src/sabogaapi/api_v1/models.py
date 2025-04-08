"""Beanie database models."""

import datetime
from typing import Annotated, Any, List

from beanie import Document, Indexed, TimeSeriesConfig
from pydantic import BaseModel, Field


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
            bucket_rounding_second=86400,
            bucket_max_span_seconds=86400,
        )
        name = "rank_history"


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
    bgg_rank: Annotated[int, Indexed()] | None = None
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
        page_size: int = 50,
    ) -> List[dict[str, Any]]:
        find_rank_comparison = [
            {"$sort": {"bgg_rank": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
            {
                "$lookup": {
                    "from": f"{RankHistory.Settings.name}",
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$bgg_id", "$$bgg_id"]},
                                    ]
                                }
                            }
                        },
                        {"$sort": {"date": -1}},
                        {
                            "$match": {
                                "date": {"$lt": compare_to + datetime.timedelta(days=1)}
                            }
                        },
                        {"$limit": 1},
                    ],
                    "as": "rank_history",
                }
            },
            {"$unwind": {"path": "$rank_history", "preserveNullAndEmptyArrays": True}},
            {
                "$set": {
                    "bgg_rank_change": {
                        "$subtract": ["$rank_history.bgg_rank", "$bgg_rank"]
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

        return rank_data

    @staticmethod
    async def get_boardgame_with_historical_data(
        bgg_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        mode: str,
    ) -> dict | None:
        date_diff = (end_date - start_date).days
        if mode == "auto":
            if date_diff <= 30:
                mode = "daily"
            elif date_diff <= 180:
                mode = "weekly"
            else:
                mode = "yearly"

        pipeline = [
            {"$match": {"bgg_id": bgg_id}},
            {
                "$lookup": {
                    "from": f"{RankHistory.Settings.name}",
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$bgg_id", "$$bgg_id"]},
                                "date": {"$lte": end_date, "$gte": start_date},
                            }
                        },
                        {"$sort": {"date": 1}},
                    ],
                    "as": "bgg_rank_history",
                }
            },
        ]

        result = await Boardgame.aggregate(aggregation_pipeline=pipeline).to_list()

        if not result:
            return None

        boardgame_data = result[0]

        # Apply mode filtering to bgg_rank_history
        history = boardgame_data["bgg_rank_history"]
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

        boardgame_data["bgg_rank_history"] = [
            {
                "date": entry["date"].replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                "bgg_id": entry["bgg_id"],
                "bgg_rank": entry["bgg_rank"],
                "bgg_geek_rating": entry["bgg_geek_rating"],
                "bgg_average_rating": entry["bgg_average_rating"],
            }
            for entry in history
        ]
        return boardgame_data

    class Settings:
        name = "boardgames"
