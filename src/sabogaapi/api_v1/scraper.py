import argparse
import asyncio
import time
from datetime import datetime
from xml.etree import ElementTree

import requests
from pydantic import BaseModel

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.models import Boardgame, BoardgameSettings


class BoardgameBGGIDs(BaseModel):
    bgg_id: int


async def ascrape_full() -> None:
    await init_db()

    boardgame_settings = await BoardgameSettings.find_all().first_or_none()
    if boardgame_settings is None:
        boardgame_settings = BoardgameSettings(
            last_bgg_scrape=datetime.now(), last_scraped_id=0
        )
        await boardgame_settings.save()

    last_scrape_date = boardgame_settings.last_bgg_scrape
    last_scraped_id = boardgame_settings.last_scraped_id

    sync_finished = False
    while sync_finished is False:
        if (datetime.now() - last_scrape_date).seconds < 10:
            print("Waiting")
            time.sleep(10)

        step = 200
        ids = list(range(last_scraped_id + 1, last_scraped_id + (step + 1)))

        r = requests.get(f"https://boardgamegeek.com/xmlapi2/thing?id={ids[0:50]}")
        xml = ElementTree.fromstring(r.text)
        items = xml.findall("item")
        if len(items) == 0:
            sync_finished = True
        else:
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(map(str, ids))}&stats=1&type=boardgame"
            )
            xml = ElementTree.fromstring(r.text)
            items = xml.findall("item")
            print(f"Scraping {ids}", flush=True)
            bgg_id = 0
            for item in items:
                bgg_id = int(item.get("id"))
                name = ""
                for name_element in item.iter("name"):
                    if name_element.attrib["type"] == "primary":
                        name = name_element.get("value")
                ratings = item.find("statistics").find("ratings")
                average_rating = ratings.find("average").get("value")
                if average_rating is "":
                    average_rating = None
                else:
                    average_rating = float(average_rating)
                geek_rating = ratings.find("bayesaverage").get("value")
                if geek_rating is "":
                    geek_rating = None
                else:
                    geek_rating = float(geek_rating)

                rank = None
                for rank_element in ratings.iter("rank"):
                    if rank_element.attrib["name"] == "boardgame":
                        if rank_element.get("value") == "Not Ranked":
                            rank = None
                        else:
                            rank = int(rank_element.get("value"))

                boardgame = await Boardgame.find_one(Boardgame.bgg_id == bgg_id)

                if boardgame is None:
                    boardgame = Boardgame(
                        bgg_id=bgg_id,
                        name=name,
                        bgg_rank=rank,
                        bgg_rank_change=0,
                        bgg_geek_rating=geek_rating,
                        bgg_geek_rating_change=0,
                        bgg_average_rating=average_rating,
                        bgg_average_rating_change=0,
                    )
                    await boardgame.insert()
                else:
                    if (
                        boardgame.bgg_rank != rank
                        or boardgame.bgg_average_rating != average_rating
                        or boardgame.bgg_geek_rating != geek_rating
                    ):
                        print("Updating")
                        boardgame.bgg_rank_change = rank - boardgame.bgg_rank
                        boardgame.bgg_geek_rating_change = (
                            geek_rating - boardgame.bgg_geek_rating
                        )
                        boardgame.bgg_average_rating = (
                            average_rating - boardgame.bgg_average_rating
                        )
                        boardgame.bgg_rank = rank
                        boardgame.bgg_geek_rating = geek_rating
                        boardgame.bgg_average_rating = average_rating
                    await boardgame.save()

            last_scrape_date = datetime.now()
            last_scraped_id = bgg_id

    boardgame_settings.last_bgg_scrape = datetime.now()
    boardgame_settings.last_scraped_id = last_scraped_id
    await boardgame_settings.save()


async def ascrape_update():
    await init_db()

    sync_finished = False

    last_scrape_date = datetime.now()
    last_scraped_id = 0

    while sync_finished is False:
        step = 200
        ids = (
            await Boardgame.find_all()
            .project(BoardgameBGGIDs)
            .limit(step)
            .skip(last_scraped_id)
            .sort("+bgg_id")
            .to_list()
        )
        ids = list(map(lambda x: x.bgg_id, ids))

        if (datetime.now() - last_scrape_date).seconds < 10:
            print("Waiting")
            time.sleep(10)

        if len(ids) == 0:
            sync_finished = True
        else:
            r = requests.get(
                f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(map(str, ids))}&stats=1&type=boardgame"
            )
            xml = ElementTree.fromstring(r.text)
            items = xml.findall("item")
            print(f"Scraping {ids}", flush=True)
            bgg_id = 0
            for item in items:
                bgg_id = int(item.get("id"))
                name = ""
                for name_element in item.iter("name"):
                    if name_element.attrib["type"] == "primary":
                        name = name_element.get("value")
                ratings = item.find("statistics").find("ratings")
                average_rating = ratings.find("average").get("value")
                if average_rating is "":
                    average_rating = None
                else:
                    average_rating = float(average_rating)
                geek_rating = ratings.find("bayesaverage").get("value")
                if geek_rating is "":
                    geek_rating = None
                else:
                    geek_rating = float(geek_rating)

                rank = None
                for rank_element in ratings.iter("rank"):
                    if rank_element.attrib["name"] == "boardgame":
                        if rank_element.get("value") == "Not Ranked":
                            rank = None
                        else:
                            rank = int(rank_element.get("value"))

                boardgame = await Boardgame.find_one(Boardgame.bgg_id == bgg_id)

                if (
                    boardgame.bgg_rank != rank
                    or boardgame.bgg_average_rating != average_rating
                    or boardgame.bgg_geek_rating != geek_rating
                ):
                    boardgame.bgg_rank_change = rank - boardgame.bgg_rank
                    boardgame.bgg_geek_rating_change = (
                        geek_rating - boardgame.bgg_geek_rating
                    )
                    boardgame.bgg_average_rating = (
                        average_rating - boardgame.bgg_average_rating
                    )
                    boardgame.bgg_rank = rank
                    boardgame.bgg_geek_rating = geek_rating
                    boardgame.bgg_average_rating = average_rating
                    await boardgame.save()

            last_scrape_date = datetime.now()
            last_scraped_id = bgg_id


def scrape():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.full is True:
        asyncio.run(ascrape_full())
    else:
        asyncio.run(ascrape_update())
