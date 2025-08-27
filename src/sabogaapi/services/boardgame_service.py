import datetime

from sabogaapi import models, schemas
from sabogaapi.logger import configure_logger

logger = configure_logger()


class BoardgameService:
    @staticmethod
    async def get_top_ranked_boardgames(
        compare_to: datetime.datetime,
        page: int = 1,
        page_size: int = 50,
    ) -> list[schemas.BoardgameInList]:
        logger.debug(
            "Fetching top ranked boardgames",
            extra={
                "compare_to": compare_to.isoformat(),
                "page": page,
                "page_size": page_size,
            },
        )

        find_rank_comparison = [
            {"$sort": {"bgg_rank": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
            {
                "$lookup": {
                    "from": f"{models.RankHistory.Settings.name}",
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$bgg_id", "$$bgg_id"]},
                                    ],
                                },
                            },
                        },
                        {"$sort": {"date": -1}},
                        {
                            "$match": {
                                "date": {
                                    "$lt": compare_to + datetime.timedelta(days=1)
                                },
                            },
                        },
                        {"$limit": 1},
                    ],
                    "as": "rank_history",
                },
            },
            {"$unwind": {"path": "$rank_history", "preserveNullAndEmptyArrays": True}},
            {
                "$set": {
                    "bgg_rank_change": {
                        "$subtract": ["$rank_history.bgg_rank", "$bgg_rank"],
                    },
                    "bgg_average_rating_change": {
                        "$subtract": [
                            "$bgg_average_rating",
                            "$rank_history.bgg_average_rating",
                        ],
                    },
                    "bgg_geek_rating_change": {
                        "$subtract": [
                            "$bgg_geek_rating",
                            "$rank_history.bgg_geek_rating",
                        ],
                    },
                },
            },
        ]

        rank_data = await models.Boardgame.aggregate(
            aggregation_pipeline=find_rank_comparison,
        ).to_list()
        logger.info(
            "Top ranked boardgames fetched",
            extra={
                "returned_count": len(rank_data),
                "page": page,
                "page_size": page_size,
            },
        )
        return [schemas.BoardgameInList(**result) for result in rank_data]

    @staticmethod
    async def get_boardgame_with_historical_data(
        bgg_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        mode: str,
    ) -> schemas.BoardgameSingle | None:
        """Get a boardgame with historical data.

        Args:
            bgg_id (int): ID.
            start_date (datetime.datetime): Start date for historical data.
            end_date (datetime.datetime): End date for historical data.
            mode (str): Mode for historical data.

        Returns:
            schemas.BoardgameSingle | None: Boardgame or none if there is no result.

        """
        logger.debug(
            "Fetching boardgame with historical data",
            extra={
                "bgg_id": bgg_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "mode": mode,
            },
        )
        date_diff = (end_date - start_date).days
        if mode == "auto":
            if date_diff <= 30:
                mode = "daily"
            elif date_diff <= 180:
                mode = "weekly"
            else:
                mode = "yearly"
            logger.debug(
                "Auto-detected mode",
                extra={"mode": mode, "date_diff_days": date_diff},
            )

        pipeline = [
            {"$match": {"bgg_id": bgg_id}},
            {
                "$lookup": {
                    "from": f"{models.RankHistory.Settings.name}",
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$bgg_id", "$$bgg_id"]},
                                "date": {"$lte": end_date, "$gte": start_date},
                            },
                        },
                        {"$sort": {"date": 1}},
                    ],
                    "as": "bgg_rank_history",
                },
            },
            {
                "$lookup": {
                    "from": f"{models.Designer.Settings.name}",
                    "localField": "designers.$id",
                    "foreignField": "_id",
                    "as": "designers",
                },
            },
            {
                "$lookup": {
                    "from": f"{models.Family.Settings.name}",
                    "localField": "families.$id",
                    "foreignField": "_id",
                    "as": "families",
                },
            },
            {
                "$lookup": {
                    "from": f"{models.Category.Settings.name}",
                    "localField": "categories.$id",
                    "foreignField": "_id",
                    "as": "categories",
                },
            },
            {
                "$lookup": {
                    "from": f"{models.Mechanic.Settings.name}",
                    "localField": "mechanics.$id",
                    "foreignField": "_id",
                    "as": "mechanics",
                },
            },
        ]

        result = await models.Boardgame.aggregate(
            aggregation_pipeline=pipeline
        ).to_list()

        if not result:
            logger.warning("No boardgame found with bgg_id", extra={"bgg_id": bgg_id})
            return None

        boardgame_data = result[0]

        # Apply mode filtering to bgg_rank_history
        history = boardgame_data["bgg_rank_history"]
        if mode == "weekly":
            history = history[::-7]
        elif mode == "yearly":
            seen_years = set()
            yearly_history = []
            for entry in reversed(history):
                year = entry["date"].year
                if year not in seen_years:
                    yearly_history.append(entry)
                    seen_years.add(year)
            history = yearly_history

        boardgame_data["bgg_rank_history"] = [
            {
                "date": entry["date"].replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                ),
                "bgg_id": entry["bgg_id"],
                "bgg_rank": entry["bgg_rank"],
                "bgg_geek_rating": entry["bgg_geek_rating"],
                "bgg_average_rating": entry["bgg_average_rating"],
            }
            for entry in history
        ]
        logger.info(
            "Boardgame with historical data returned",
            extra={
                "bgg_id": bgg_id,
                "history_points": len(boardgame_data["bgg_rank_history"]),
                "mode": mode,
            },
        )
        return schemas.BoardgameSingle(**boardgame_data)

    @staticmethod
    async def get_total_count() -> int:
        """Get number of boardgames.

        Returns:
            int: Number of boardgames.

        """
        return await models.Boardgame.find_all().count()

    @staticmethod
    async def get_trending_games(limit: int = 5) -> list[schemas.BoardgameInList]:
        """Get trending games.

        Args:
            limit (int, optional): Limit for number of games. Defaults to 10.

        Returns:
            list[schemas.BoardgameSingle]: List of boardgames.

        """
        compare_to = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
            days=30
        )

        pipeline = [
            {"$sort": {"mean_trend": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": models.RankHistory.Settings.name,
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$bgg_id", "$$bgg_id"]},
                                "date": {
                                    "$lt": compare_to + datetime.timedelta(days=1)
                                },
                            }
                        },
                        {"$sort": {"date": -1}},
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
        results = await models.Boardgame.aggregate(pipeline).to_list()

        return [schemas.BoardgameInList(**result) for result in results]

    @staticmethod
    async def get_declining_games(limit: int = 5) -> list[schemas.BoardgameInList]:
        """Get declining games.

        Args:
            limit (int, optional): Limit for number of games. Defaults to 10.

        Returns:
            list[schemas.BoardgameSingle]: List of boardgames.

        """
        compare_to = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
            days=30
        )

        pipeline = [
            {"$sort": {"mean_trend": 1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": models.RankHistory.Settings.name,
                    "let": {"bgg_id": "$bgg_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$bgg_id", "$$bgg_id"]},
                                "date": {
                                    "$lt": compare_to + datetime.timedelta(days=1)
                                },
                            }
                        },
                        {"$sort": {"date": -1}},
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
        results = await models.Boardgame.aggregate(pipeline).to_list()

        return [schemas.BoardgameInList(**result) for result in results]
