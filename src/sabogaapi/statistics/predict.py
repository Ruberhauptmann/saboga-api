"""Forecast function."""

from typing import cast

import numpy as np
import pandas as pd
from sktime.forecasting.statsforecast import StatsForecastAutoARIMA

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Prediction, RankHistory

logger = configure_logger()


async def forecast_game_ranking(rank_history: list[RankHistory]) -> list[Prediction]:
    """Forecast game ranking.

    Args:
        rank_history (list[RankHistory]): Data points.

    Returns:
        list[Prediction]: List with predictions.

    """
    logger.info("Starting game ranking forecast.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return []

    logger.debug("Received %s rank history records.", len(rank_history))

    df = pd.DataFrame([dict(entry) for entry in rank_history])
    df = df.dropna()
    df = df.set_index("date", drop=True)
    df.index = pd.to_datetime(df.index)
    df = df.groupby(df.index).last()
    df = df.sort_index()
    df.index = cast("pd.DatetimeIndex", df.index).to_period("D")

    fh = np.arange(1, 31)

    forecaster = StatsForecastAutoARIMA()
    logger.info("Fitting StatsForecastAutoARIMA model.")
    forecaster.fit(df)

    logger.info("Generating point forecasts.")
    y_pred = forecaster.predict(fh=fh)
    interval = 0.95
    conf_int = forecaster.predict_interval(fh=fh, coverage=interval)
    conf_int.columns = [
        "_".join(map(str, col)) if isinstance(col, tuple) else col
        for col in conf_int.columns
    ]

    merged_df = y_pred.merge(conf_int, left_index=True, right_index=True)

    cols = [
        "bgg_rank",
        f"bgg_rank_{interval}_lower",
        f"bgg_rank_{interval}_upper",
        "bgg_average_rating",
        f"bgg_average_rating_{interval}_lower",
        f"bgg_average_rating_{interval}_upper",
        "bgg_geek_rating",
        f"bgg_geek_rating_{interval}_lower",
        f"bgg_geek_rating_{interval}_upper",
    ]
    zipped = zip(merged_df.index, *(merged_df[c] for c in cols), strict=False)

    predictions = [
        Prediction(
            date=date.to_timestamp(),
            bgg_rank=int(round(rank, 0)),
            bgg_rank_confidence_interval=(rank_lower, rank_upper),
            bgg_average_rating=avg_rating,
            bgg_average_rating_confidence_interval=(avg_low, avg_up),
            bgg_geek_rating=geek_rating,
            bgg_geek_rating_confidence_interval=(geek_low, geek_up),
        )
        for (
            date,
            rank,
            rank_lower,
            rank_upper,
            avg_rating,
            avg_low,
            avg_up,
            geek_rating,
            geek_low,
            geek_up,
        ) in zipped
    ]

    logger.info("Generated %s forecast predictions.", len(predictions))
    return predictions
