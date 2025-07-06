import os
import time
from datetime import datetime
from zipfile import ZipFile

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from sabogaapi.api_v1.config import settings
from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, RankHistory
from sabogaapi.logger import configure_logger

logger = configure_logger()


def download_zip():
    # Set up download directory
    download_dir = os.path.abspath("download")
    os.makedirs(download_dir, exist_ok=True)

    # Firefox options
    options = Options()
    options.add_argument("--headless")  # Uncomment to run without browser window

    options.set_preference("browser.download.folderList", 2)  # Use custom download path
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("pdfjs.disabled", True)

    # Start browser
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()), options=options
    )

    driver.get("https://boardgamegeek.com/login")
    time.sleep(2)

    cookie_button = driver.find_element(By.CLASS_NAME, "fc-cta-consent")
    cookie_button.click()

    username = settings.bgg_username
    password = settings.bgg_password

    driver.find_element(By.ID, "inputUsername").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()

    time.sleep(5)

    driver.get("https://boardgamegeek.com/data_dumps/bg_ranks")
    time.sleep(3)

    link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "Click to Download")
    s3_url = link_element.get_attribute("href")
    driver.quit()

    response = requests.get(s3_url)
    filename = os.path.join(download_dir, "boardgame_ranks.zip")
    with open(filename, "wb") as f:
        f.write(response.content)

    with ZipFile(filename) as csv_zip:
        with csv_zip.open("boardgames_ranks.csv") as rank_csv_file:
            df = pd.read_csv(rank_csv_file)[lambda x: x["rank"] != 0]

    return df


async def ascrape_update() -> None:
    await init_db()

    date = datetime.today()

    games_df = download_zip()

    new_games = []
    for game in games_df.itertuples():
        game_db = await Boardgame.find_one(Boardgame.bgg_id == game.id)

        if game_db:
            game_db.name = game.name
            game_db.bgg_rank = game.rank
            game_db.bgg_geek_rating = game.bayesaverage
            game_db.bgg_average_rating = game.average
            game_db.year_published = game.yearpublished
            await game_db.save()
        else:
            new_games.append(
                Boardgame(
                    bgg_id=game.id,
                    name=game.name,
                    bgg_rank=game.rank,
                    bgg_geek_rating=game.bayesaverage,
                    bgg_average_rating=game.average,
                    year_published=game.yearpublished,
                )
            )
    if new_games:
        await Boardgame.insert_many(new_games)

    new_rank_history = [
        RankHistory(
            date=date,
            bgg_id=entry.id,
            bgg_rank=entry.rank,
            bgg_geek_rating=entry.bayesaverage,
            bgg_average_rating=entry.average,
        )
        for entry in games_df.itertuples()
    ]

    if new_rank_history:
        await RankHistory.insert_many(new_rank_history)
