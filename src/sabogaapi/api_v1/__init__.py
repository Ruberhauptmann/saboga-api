"""Version 1 of the saboga API."""
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from sabogaapi.api_v1.routers import boardgames

description = """
This is a little project utilising data from Boardgamegeek to show historical rating and rank data of the ranked games.

<a href="https://boardgamegeek.com" target="_blank">
    <img alt="Powered by Boardgamegeek" src="/api/v1/static/powered_by_bgg.webp" width="200">
</a>
"""

api_v1 = FastAPI(
    title="saboga API v1",
    description=description,
    contact={
        "name": "Tjark Sievers",
        "url": "https://tjarksievers.de/about",
        "email": "tjarksievers@icloud.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/Ruberhauptmann/saboga-api/blob/main/LICENSE.md",
    },
)

api_v1.include_router(boardgames.router)
api_v1.mount("/static", StaticFiles(directory="static"), name="static")
