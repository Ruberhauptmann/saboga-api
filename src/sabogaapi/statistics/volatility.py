"""Calculate volatility."""

import pandas as pd

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import RankHistory

logger = configure_logger()


def calculate_volatility(
    rank_history: list[RankHistory],
) -> tuple[float, float, float] | tuple[None, None, None]:
    """Calculate volatility.

    Args:
        rank_history (list[RankHistory]): List of data entries.

    Returns:
        tuple[float, float, float]: Volatility for rank, geek_rating and average_rating.

    """
    logger.info("Starting volatility calculation.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return None, None, None

    logger.debug("Received %s rank history records.", len(rank_history))

    df = pd.DataFrame([dict(entry) for entry in rank_history]).dropna()

    rank_volatility = df["bgg_rank"].std() / df["bgg_rank"].mean()
    geek_rating_volatility = df["bgg_geek_rating"].std() / df["bgg_geek_rating"].mean()
    average_rating_volatility = (
        df["bgg_average_rating"].std() / df["bgg_average_rating"].mean()
    )

    return rank_volatility, geek_rating_volatility, average_rating_volatility
