from typing import List, cast

import numpy as np
import pandas as pd
from sktime.forecasting.statsforecast import StatsForecastAutoARIMA

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Prediction, RankHistory

logger = configure_logger()


async def forecast_game_ranking(rank_history: List[RankHistory]) -> List[Prediction]:
    logger.info("Starting game ranking forecast.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return []

    logger.debug(f"Received {len(rank_history)} rank history records.")

    df = pd.DataFrame([dict(entry) for entry in rank_history])
    df.drop(columns=["id", "revision_id"], inplace=True)
    df.dropna(inplace=True)
    df.set_index("date", inplace=True, drop=True)
    df.index = pd.to_datetime(df.index)
    df = df.groupby(df.index).last()
    df.sort_index(inplace=True)
    df.index = cast(pd.DatetimeIndex, df.index).to_period("D")

    print(df, flush=True)

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

    merged_df = pd.merge(y_pred, conf_int, left_index=True, right_index=True)
    predictions = [
        Prediction(
            date=date.to_timestamp(),
            bgg_rank=int(round(rank, 0)),
            bgg_rank_confidence_interval=(rank_lower, rank_upper),
            bgg_average_rating=average_rating,
            bgg_average_rating_confidence_interval=(
                average_rating_lower,
                average_rating_upper,
            ),
            bgg_geek_rating=geek_rating,
            bgg_geek_rating_confidence_interval=(geek_rating_lower, geek_rating_upper),
        )
        for date, rank, rank_lower, rank_upper, average_rating, average_rating_lower, average_rating_upper, geek_rating, geek_rating_lower, geek_rating_upper in zip(
            merged_df.index,
            merged_df["bgg_rank"],
            merged_df[f"bgg_rank_{interval}_lower"],
            merged_df[f"bgg_rank_{interval}_upper"],
            merged_df["bgg_average_rating"],
            merged_df[f"bgg_average_rating_{interval}_lower"],
            merged_df[f"bgg_average_rating_{interval}_upper"],
            merged_df["bgg_geek_rating"],
            merged_df[f"bgg_geek_rating_{interval}_lower"],
            merged_df[f"bgg_geek_rating_{interval}_upper"],
        )
    ]

    logger.info(f"Generated {len(predictions)} forecast predictions.")
    return predictions
