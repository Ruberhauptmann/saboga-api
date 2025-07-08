from typing import List

import pandas as pd

from sabogaapi.api_v1.models import RankHistory
from sabogaapi.logger import configure_logger

logger = configure_logger()


def calculate_volatility(rank_history: List[RankHistory]):
    logger.info("Starting volatility calculation.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return []

    logger.debug(f"Received {len(rank_history)} rank history records.")

    df = pd.DataFrame([dict(entry) for entry in rank_history])
    df.drop(columns=["id", "revision_id"], inplace=True)
    df.dropna(inplace=True)

    rank_volatility = df["bgg_rank"].std() / df["bgg_rank"].mean()
    geek_rating_volatility = df["bgg_geek_rating"].std() / df["bgg_geek_rating"].mean()
    average_rating_volatility = (
        df["bgg_average_rating"].std() / df["bgg_average_rating"].mean()
    )

    return rank_volatility, geek_rating_volatility, average_rating_volatility
