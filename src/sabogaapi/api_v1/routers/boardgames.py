import math
import re
from datetime import datetime
from typing import List

import requests
from beanie import PydanticObjectId
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Request, Response

from sabogaapi.api_v1.models import Boardgame, BoardgameSettings, RatingHistory
from sabogaapi.api_v1.schemas import BoardgamePublic

router = APIRouter(
    prefix="/boardgames",
    tags=["Boardgames"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[BoardgamePublic])
async def read_all_games(
    response: Response,
    request: Request,
    page: int = 1,
    per_page: int = 100,
    scrape: bool = True,
) -> List[Boardgame]:
    if scrape is True:
        await sync_ranking_data_from_bgg()

    total_count = await Boardgame.count()
    skip = (page - 1) * per_page
    games = await Boardgame.find_all().skip(skip).limit(per_page).to_list()

    last_page = math.ceil(total_count / per_page)
    response.headers["link"] = ""

    if page > 1:
        response.headers[
            "link"
        ] += f'<{request.url_for("read_all_games").include_query_params(page=page-1, per_page=per_page)}>; rel="prev",'
    if page < last_page:
        response.headers[
            "link"
        ] += f'<{request.url_for("read_all_games").include_query_params(page=page+1, per_page=per_page)}>; rel="next",'
    response.headers["link"] += (
        f'<{request.url_for("read_all_games").include_query_params(page=last_page, per_page=per_page)}>; rel="last",'
        f'<{request.url_for("read_all_games").include_query_params(page=0, per_page=per_page)}>; rel="first",'
    )

    return games


async def sync_ranking_data_from_bgg() -> None:
    boardgame_settings = await BoardgameSettings.find_all().first_or_none()
    if boardgame_settings is None:
        boardgame_settings = BoardgameSettings(
            last_bgg_ranking_scrape=datetime.now(), last_bgg_scrape_page=1
        )
        await boardgame_settings.save()

    if (datetime.now() - boardgame_settings.last_bgg_ranking_scrape).seconds > 10:
        browse_page = requests.get(
            f"https://boardgamegeek.com/browse/boardgame/page/{boardgame_settings.last_bgg_scrape_page}"
        )
        soup = BeautifulSoup(markup=browse_page.text, features="html.parser")
        rows = soup.find_all("tr", id=re.compile("^row"))
        for row in rows:
            bgg_rank = int(
                row.find(name="td", class_="collection_rank").get_text().strip()
            )
            bgg_id = int(
                row.find(name="a", class_="primary")["href"].split("/")[2].strip()
            )
            game = await Boardgame.find(Boardgame.bgg_id == bgg_id).first_or_none()
            if not game:
                game = Boardgame(bgg_id=bgg_id)

            if len(game.bgg_rank) == 0:
                ranking = RatingHistory(date=datetime.now(), rank=bgg_rank, change=0)
                game.bgg_rank.append(ranking)
            else:
                last_ranking = game.bgg_rank[-1]
                if last_ranking.rank != bgg_rank:
                    ranking = RatingHistory(
                        date=datetime.now(),
                        rank=bgg_rank,
                        change=last_ranking.rank - bgg_rank,
                    )
                    game.bgg_rank.append(ranking)

            await game.save()

        boardgame_settings.last_bgg_ranking_scrape = datetime.now()
        if boardgame_settings.last_bgg_scrape_page == boardgame_settings.max_bgg_scrape:
            boardgame_settings.last_bgg_scrape_page = 0
        else:
            boardgame_settings.last_bgg_scrape_page += 1
        await boardgame_settings.save()


@router.get("/{game_id}", response_model=BoardgamePublic)
async def read_game(game_id: PydanticObjectId) -> Boardgame:
    game = await Boardgame.get(game_id, fetch_links=True)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
