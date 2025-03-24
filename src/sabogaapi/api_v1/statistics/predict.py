from typing import List

import numpy as np
import pandas as pd
from sktime.forecasting.statsforecast import StatsForecastAutoARIMA

from sabogaapi.api_v1.schemas import Prediction, RankHistory


async def forecast_game_ranking(rank_history: List[RankHistory]) -> List[Prediction]:
    df = pd.DataFrame(
        [{"date": entry.date.date(), "rank": entry.bgg_rank} for entry in rank_history]
    )
    df["date"] = pd.to_datetime(df["date"])

    df.set_index("date", inplace=True)
    df = df.groupby(df.index).last()
    df.index = df.index.to_period("D")
    df.sort_index(inplace=True)

    fh = np.arange(1, 31)

    forecaster = StatsForecastAutoARIMA()
    forecaster.fit(df)
    y_pred = forecaster.predict(fh=fh).round(0).astype(int)
    interval = 0.95
    conf_int = forecaster.predict_interval(fh=fh, coverage=interval)

    merged_df = pd.merge(
        y_pred, conf_int["rank", f"{interval}"], left_index=True, right_index=True
    )
    predictions = [
        Prediction(
            date=row.to_timestamp(),
            rank_prediction=rank,
            rank_confidence_interval=(lower, upper),
        )
        for row, rank, lower, upper in zip(
            merged_df.index, merged_df["rank"], merged_df["lower"], merged_df["upper"]
        )
    ]

    return predictions
