"""Version 1 of the saboga API."""

from fastapi import APIRouter

from sabogaapi.api_v1.routers import (
    boardgames,
    categories,
    designers,
    families,
    mechanics,
    search,
    single_game,
)

description = """
This is a little project utilising data from Boardgamegeek to show historical rating and rank data of the ranked games.

<a href="https://boardgamegeek.com" target="_blank">
    <img alt="Powered by Boardgamegeek" src="/api/v1/static/powered_by_bgg.webp" width="200">
</a>
"""

api_v1 = APIRouter()

api_v1.include_router(boardgames.router)
api_v1.include_router(single_game.router)

api_v1.include_router(categories.router)
api_v1.include_router(designers.router)
api_v1.include_router(families.router)
api_v1.include_router(mechanics.router)

api_v1.include_router(search.router)
