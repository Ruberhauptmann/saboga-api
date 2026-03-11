"""Calculate volatility for rank and rating history."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_volatility(
    rank_history: list[dict],
) -> tuple[float, float, float] | tuple[None, None, None]:
    """Calculate volatility.

    Args:
        rank_history (list[dict]): List of entries with keys ``bgg_rank``,
            ``bgg_geek_rating`` and ``bgg_average_rating``.

    Returns:
        tuple[float, float, float]: Volatility for rank, geek_rating and
            average_rating, or ``(None, None, None)`` if there's no data.
    """
    logger.info("Starting volatility calculation.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return None, None, None

    logger.debug("Received %s rank history records.", len(rank_history))

    df = pd.DataFrame(rank_history[-30:]).dropna()

    rank_volatility = df["bgg_rank"].std() / df["bgg_rank"].mean()
    geek_rating_volatility = df["bgg_geek_rating"].std() / df["bgg_geek_rating"].mean()
    average_rating_volatility = (
        df["bgg_average_rating"].std() / df["bgg_average_rating"].mean()
    )

    return rank_volatility, geek_rating_volatility, average_rating_volatility
