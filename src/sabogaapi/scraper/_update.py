import datetime
import time
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

import numpy as np
import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload
from webdriver_manager.firefox import GeckoDriverManager

from sabogaapi import models, schemas
from sabogaapi.config import settings
from sabogaapi.database import sessionmanager
from sabogaapi.logger import configure_logger
from sabogaapi.statistics.trending import calculate_trends
from sabogaapi.statistics.volatility import calculate_volatility

logger = configure_logger()


def download_zip() -> pd.DataFrame:  # pragma: no cover
    logger.info("Starting ZIP download process")

    download_dir = Path("download").resolve()
    download_dir.mkdir(parents=True, exist_ok=True)

    # Firefox options
    options = Options()
    options.add_argument("--headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", f"{download_dir}")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.set_preference("browser.download.manager.showWhenStarting", value=False)
    options.set_preference("pdfjs.disabled", value=True)

    logger.info("Launching headless Firefox browser")
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options,
    )
    try:
        logger.info("Navigating to BGG login page")
        driver.get("https://boardgamegeek.com/login")
        time.sleep(2)

        for selector in ["fc-cta-consent", "c-s-bn"]:
            try:
                button = driver.find_element(By.CLASS_NAME, selector)
                button.click()
                logger.debug("Clicked cookie consent: %s", selector)
                time.sleep(1)
            except NoSuchElementException:
                pass

        username = settings.bgg_username
        password = settings.bgg_password

        driver.find_element(By.ID, "inputUsername").send_keys(username)
        driver.find_element(By.ID, "inputPassword").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()

        logger.info("Login submitted. Waiting for redirect")
        time.sleep(5)

        driver.get("https://boardgamegeek.com/data_dumps/bg_ranks")
        time.sleep(3)

        logger.info("Fetching S3 URL for ZIP download")
        link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Click to Download")
        s3_url = link_element.get_attribute("href")
        logger.debug("S3 URL: %s", s3_url)
    finally:
        driver.quit()
        logger.debug("Browser closed.")

    logger.info("Downloading ZIP file")
    response = requests.get(str(s3_url), timeout=30)
    filename = Path(download_dir) / "boardgame_ranks.zip"
    with filename.open("wb") as f:
        f.write(response.content)

    with (
        ZipFile(filename) as csv_zip,
        csv_zip.open("boardgames_ranks.csv") as rank_csv_file,
    ):
        df = pd.read_csv(rank_csv_file)

    df = df[df["rank"] != 0]
    logger.info("Parsed %s ranked boardgames from CSV.", len(df))

    return df


async def insert_games(games_df: pd.DataFrame) -> tuple[list[Any], int]:
    logger.info("Processing boardgames from CSV.")

    date = datetime.datetime.now(tz=datetime.UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    updated_games = 0
    new_games: list[models.Boardgame] = []

    async with sessionmanager.session() as session:
        for game in games_df.itertuples():
            result = await session.execute(
                select(models.Boardgame).where(models.Boardgame.bgg_id == game.id)
            )
            game_db: models.Boardgame | None = result.scalar_one_or_none()

            raw_rank = cast("float | int | None", game.rank)
            raw_bayes = cast("float | None", game.bayesaverage)
            raw_average = cast("float | None", game.average)
            raw_year = cast("int | None", game.yearpublished)
            raw_name = cast("str", game.name)

            name = str(raw_name)
            rank = (
                int(raw_rank)
                if raw_rank is not None and not pd.isna(raw_rank)
                else None
            )
            geek_rating = (
                float(raw_bayes)
                if raw_bayes is not None and not pd.isna(raw_bayes)
                else None
            )
            avg_rating = (
                float(raw_average)
                if raw_average is not None and not pd.isna(raw_average)
                else None
            )
            year = (
                int(raw_year)
                if raw_year is not None and not pd.isna(raw_year)
                else None
            )

            if game_db:
                game_db.name = name
                game_db.bgg_rank = rank
                game_db.bgg_geek_rating = geek_rating
                game_db.bgg_average_rating = avg_rating
                game_db.year_published = year
                updated_games += 1
            else:
                game_db = models.Boardgame(
                    bgg_id=game.id,
                    name=game.name,
                    bgg_rank=game.rank,
                    bgg_geek_rating=game.bayesaverage,
                    bgg_average_rating=game.average,
                    year_published=game.yearpublished,
                )
                session.add(game_db)
                await session.flush()

            rank_exists = await session.scalar(
                select(models.RankHistory.id).where(
                    and_(
                        models.RankHistory.boardgame_id == game_db.id,
                        models.RankHistory.date == date,
                    )
                )
            )

            if not rank_exists:
                new_rank_history = models.RankHistory(
                    date=date,
                    boardgame=game_db,
                    bgg_rank=game.rank,
                    bgg_geek_rating=game.bayesaverage,
                    bgg_average_rating=game.average,
                )
                session.add(new_rank_history)

            await session.commit()

        # Retrieve all boardgames to update statistics
        all_games = (await session.scalars(select(models.Boardgame))).all()

        for game in all_games:
            rank_history = (
                await session.scalars(
                    select(models.RankHistory)
                    .where(models.RankHistory.boardgame_id == game.id)
                    .options(selectinload(models.RankHistory.boardgame))
                )
            ).all()

            # Compute volatility
            rank_volatility, geek_rating_volatility, average_rating_volatility = (
                calculate_volatility(
                    [schemas.RankHistory.from_orm(entry) for entry in rank_history]
                )
            )
            game.bgg_rank_volatility = np.nan_to_num(rank_volatility or 0)
            game.bgg_geek_rating_volatility = np.nan_to_num(geek_rating_volatility or 0)
            game.bgg_average_rating_volatility = np.nan_to_num(
                average_rating_volatility or 0
            )

            # Compute trends
            rank_trend, geek_rating_trend, average_rating_trend, mean_trend = (
                calculate_trends(
                    [schemas.RankHistory.from_orm(entry) for entry in rank_history]
                )
            )
            game.bgg_rank_trend = np.nan_to_num(rank_trend or 0)
            game.bgg_geek_rating_trend = np.nan_to_num(geek_rating_trend or 0)
            game.bgg_average_rating_trend = np.nan_to_num(average_rating_trend or 0)
            game.mean_trend = np.nan_to_num(mean_trend or 0)

        await session.commit()

    return new_games, updated_games


async def ascrape_update() -> None:  # pragma: no cover
    logger.info("Starting scrape process.")
    games_df = download_zip()

    new_games, updated_games = await insert_games(games_df)

    logger.info("Inserted %s new boardgames.", len(new_games))
    logger.info("Updated %s existing boardgames.", updated_games)
