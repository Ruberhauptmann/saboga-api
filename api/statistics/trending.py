"""Calculate trends for rank and rating history."""

import datetime
import logging

import numpy as np
import pandas as pd
from scipy.stats import linregress

logger = logging.getLogger(__name__)


def calculate_trends(
    rank_history: list[dict],
) -> tuple[float, float, float, float] | tuple[None, None, None, None]:
    """Calculate trends.

    Args:
        rank_history (list[dict]): List of entries with keys ``date``, ``bgg_rank``,
            ``bgg_geek_rating`` and ``bgg_average_rating``.

    Returns:
        tuple[float, float, float, float]: Trends for rank, geek_rating,
            average_rating and mean trend. If there is insufficient data all
            values are ``None``.
    """
    logger.info("Starting trend calculation.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return None, None, None, None
    if len(rank_history) < 5:
        logger.warning("Not enough rank history data provided.")
        return None, None, None, None

    logger.debug("Received %s rank history records.", len(rank_history))

    df = pd.DataFrame(rank_history[-30:]).dropna()

    rank_linfit = linregress(df["date"].apply(lambda d: d.toordinal()), df["bgg_rank"])
    geek_rating_linfit = linregress(
        df["date"].apply(lambda d: d.toordinal()), df["bgg_geek_rating"]
    )
    average_rating_linfit = linregress(
        df["date"].apply(lambda d: d.toordinal()), df["bgg_average_rating"]
    )
    days_span = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    mean_rank = df["bgg_rank"].mean()
    mean_geek_rating = df["bgg_geek_rating"].mean()
    mean_average_rating = df["bgg_average_rating"].mean()

    rank_trend = (-rank_linfit.slope * days_span) / mean_rank * 100
    geek_rating_trend = (geek_rating_linfit.slope * days_span) / mean_geek_rating * 100
    average_rating_trend = (
        (average_rating_linfit.slope * days_span) / mean_average_rating * 100
    )

    mean_trend = float(
        np.mean(np.array([rank_trend, geek_rating_trend, average_rating_trend]))
    )

    return rank_trend, geek_rating_trend, average_rating_trend, mean_trend
