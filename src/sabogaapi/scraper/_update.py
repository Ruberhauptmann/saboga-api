import datetime
import time
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from sabogaapi import models, schemas
from sabogaapi.config import settings
from sabogaapi.database import init_db
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
    options.add_argument("--headless")  # Uncomment to run without browser window

    options.set_preference("browser.download.folderList", 2)  # Use custom download path
    options.set_preference("browser.download.dir", f"{download_dir}")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.set_preference("browser.download.manager.showWhenStarting", value=False)
    options.set_preference("pdfjs.disabled", value=True)

    logger.info("Launching headless Firefox browser")
    # Start browser
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options,
    )
    try:
        logger.info("Navigating to BGG login page")
        driver.get("https://boardgamegeek.com/login")
        time.sleep(2)

        cookie_button = driver.find_element(By.CLASS_NAME, "fc-cta-consent")
        cookie_button.click()
        logger.debug("Cookie consent clicked.")

        username = settings.bgg_username
        password = settings.bgg_password

        driver.find_element(By.ID, "inputUsername").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
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


async def ascrape_update() -> None:  # pragma: no cover
    logger.info("Starting scrape. Initializing DB connection.")
    await init_db()

    date = datetime.datetime.now(tz=datetime.UTC)

    games_df = download_zip()
    updated_games = 0

    logger.info("Processing boardgames from CSV.")
    new_games = []
    for game in games_df.itertuples():
        game_db = await models.Boardgame.find_one(models.Boardgame.bgg_id == game.id)

        if game_db:
            game_db.name = game.name
            game_db.bgg_rank = game.rank
            game_db.bgg_geek_rating = game.bayesaverage
            game_db.bgg_average_rating = game.average
            game_db.year_published = game.yearpublished
            await game_db.save()
            updated_games += 1
        else:
            new_games.append(
                models.Boardgame(
                    bgg_id=game.id,
                    name=game.name,
                    bgg_rank=game.rank,
                    bgg_geek_rating=game.bayesaverage,
                    bgg_average_rating=game.average,
                    year_published=game.yearpublished,
                ),
            )
    if new_games:
        await models.Boardgame.insert_many(new_games)
        logger.info("Inserted %s new boardgames.", len(new_games))
    logger.info("Updated %s existing boardgames.", updated_games)

    new_rank_history = [
        models.RankHistory(
            date=date,
            bgg_id=entry.id,
            bgg_rank=entry.rank,
            bgg_geek_rating=entry.bayesaverage,
            bgg_average_rating=entry.average,
        )
        for entry in games_df.itertuples()
    ]

    if new_rank_history:
        await models.RankHistory.insert_many(new_rank_history)
        logger.info("Inserted %s rank history entries.", len(new_rank_history))

    all_games = await models.Boardgame.find().to_list()

    for game in all_games:
        rank_history = await models.RankHistory.find(
            models.RankHistory.bgg_id == game.bgg_id,
        ).to_list()
        rank_volatility, geek_rating_volatility, average_rating_volatility = (
            calculate_volatility(
                [schemas.RankHistory(**entry.model_dump()) for entry in rank_history],
            )
        )
        game.bgg_rank_volatility = rank_volatility
        game.bgg_geek_rating_volatility = geek_rating_volatility
        game.bgg_average_rating_volatility = average_rating_volatility

        calculate_trends(
            [schemas.RankHistory(**entry.model_dump()) for entry in rank_history]
        )

        await game.save()
