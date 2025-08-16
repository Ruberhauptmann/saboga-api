import datetime

import pandas as pd
from scipy.stats import linregress

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import RankHistory

logger = configure_logger()


def calculate_trends(rank_history: list[RankHistory]):
    logger.info("Starting trend calculation.")

    if not rank_history:
        logger.warning("No rank history data provided.")
        return []

    logger.debug(f"Received {len(rank_history)} rank history records.")

    df = pd.DataFrame([dict(entry) for entry in rank_history]).dropna()

    rank_linfit = linregress(df["date"].apply(datetime.date.toordinal), df["bgg_rank"])
    geek_rating_linfit = linregress(
        df["date"].apply(datetime.date.toordinal), df["bgg_geek_rating"]
    )
    average_rating_linfit = linregress(
        df["date"].apply(datetime.date.toordinal), df["bgg_average_rating"]
    )

    return rank_linfit.slope, geek_rating_linfit.slope, average_rating_linfit.slope
