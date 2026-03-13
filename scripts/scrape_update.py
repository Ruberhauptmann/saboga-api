import time
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import numpy as np
import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from django.utils import timezone

from api import models
from django.conf import settings as django_settings
from api.logger import configure_logger
from api.statistics.trending import calculate_trends
from api.statistics.volatility import calculate_volatility

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

        for selector in ["fc-cta-consent", "c-p-bn"]:
            try:
                button = driver.find_element(By.CLASS_NAME, selector)
                button.click()
                logger.debug("Clicked cookie consent: %s", selector)
                time.sleep(1)
            except NoSuchElementException:
                pass

        username = getattr(django_settings, "BGG_USERNAME", "")
        password = getattr(django_settings, "BGG_PASSWORD", "")

        driver.find_element(By.ID, "inputUsername").send_keys(username)
        driver.find_element(By.ID, "inputPassword").send_keys(password)
        # driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
        driver.find_element(By.XPATH, '//button[text()=" Sign In "]').click()

        logger.info("Login submitted. Waiting for redirect")
        time.sleep(5)

        driver.get("https://boardgamegeek.com/data_dumps/bg_ranks")
        time.sleep(3)

        # dump HTML to file for debugging
        page_file = download_dir / "bg_ranks_page.html"
        with page_file.open("w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.debug("Saved page source to %s", page_file)

        logger.info("Fetching S3 URL for ZIP download")
        link_element = driver.find_element(By.LINK_TEXT, "Click to Download")
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


def insert_games(games_df: pd.DataFrame) -> tuple[list[models.Boardgame], int]:
    """Insert or update boardgames based on a BGG ranks DataFrame.

    This function is synchronous and uses the Django ORM directly.
    """
    logger.info("Processing boardgames from CSV.")
    date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    updated_games = 0
    new_games: list[models.Boardgame] = []

    for game in games_df.itertuples():
        raw_rank = cast("float | int | None", game.rank)
        raw_bayes = cast("float | None", game.bayesaverage)
        raw_average = cast("float | None", game.average)
        raw_year = cast("int | None", game.yearpublished)
        raw_name = cast("str", game.name)

        name = str(raw_name)
        rank = int(raw_rank) if raw_rank is not None and not pd.isna(raw_rank) else None
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
        year = int(raw_year) if raw_year is not None and not pd.isna(raw_year) else None

        try:
            game_db = models.Boardgame.objects.get(bgg_id=game.id)
            game_db.name = name
            game_db.bgg_rank = rank
            game_db.bgg_geek_rating = geek_rating
            game_db.bgg_average_rating = avg_rating
            game_db.year_published = year
            game_db.save()
            updated_games += 1
        except models.Boardgame.DoesNotExist:
            game_db = models.Boardgame.objects.create(
                bgg_id=game.id,
                name=name,
                bgg_rank=rank,
                bgg_geek_rating=geek_rating,
                bgg_average_rating=avg_rating,
                year_published=year,
            )
            new_games.append(game_db)

        if not models.RankHistory.objects.filter(boardgame=game_db, date=date).exists():
            models.RankHistory.objects.create(
                date=date,
                boardgame=game_db,
                bgg_rank=rank,
                bgg_geek_rating=geek_rating,
                bgg_average_rating=avg_rating,
            )

    # Update statistics after all rows processed
    for game_obj in models.Boardgame.objects.all():
        history_qs = game_obj.bgg_rank_history.order_by("date").all()
        rank_list = [
            {
                "date": h.date,
                "bgg_rank": h.bgg_rank,
                "bgg_geek_rating": h.bgg_geek_rating,
                "bgg_average_rating": h.bgg_average_rating,
            }
            for h in history_qs
        ]

        rank_volatility, geek_rating_volatility, average_rating_volatility = (
            calculate_volatility(rank_list) or (None, None, None)
        )
        game_obj.bgg_rank_volatility = np.nan_to_num(rank_volatility or 0)
        game_obj.bgg_geek_rating_volatility = np.nan_to_num(geek_rating_volatility or 0)
        game_obj.bgg_average_rating_volatility = np.nan_to_num(
            average_rating_volatility or 0
        )

        rank_trend, geek_rating_trend, average_rating_trend, mean_trend = (
            calculate_trends(rank_list) or (None, None, None, None)
        )
        game_obj.bgg_rank_trend = np.nan_to_num(rank_trend or 0)
        game_obj.bgg_geek_rating_trend = np.nan_to_num(geek_rating_trend or 0)
        game_obj.bgg_average_rating_trend = np.nan_to_num(average_rating_trend or 0)
        game_obj.mean_trend = np.nan_to_num(mean_trend or 0)
        game_obj.save()

    return new_games, updated_games


def run() -> tuple[list[models.Boardgame], int]:
    """Run the full update cycle (download + insert)."""
    df = download_zip()
    return insert_games(df)
