import os
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Mapping, Optional

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from .config import settings
from .routers import (
    boardgames,
    categories,
    designers,
    families,
    mechanics,
    search,
    single_game,
)

SECRET = os.getenv("FASTAPI-USERS-SECRET")


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    extra_info: Optional[dict] = None


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]]
    | Callable[[FastAPI], AbstractAsyncContextManager[Mapping[str, Any]]]
    | None,
) -> FastAPI:
    description = """
    This is a little project utilising data from Boardgamegeek to show historical rating and rank data of the ranked games.

    <a href="https://boardgamegeek.com" target="_blank">
        <img alt="Powered by Boardgamegeek" src="/api/v1/static/powered_by_bgg.webp" width="200">
    </a>
    """
    app = FastAPI(
        title="saboga",
        contact={
            "name": "Tjark Sievers",
            "url": "https://tjarksievers.de/about",
            "email": "tjarksievers@icloud.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://github.com/Ruberhauptmann/saboga-api/blob/main/LICENSE.md",
        },
        lifespan=lifespan,
        root_path_in_servers=False,
        description=description,
    )

    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    app.mount("/img", StaticFiles(directory=settings.img_dir), name="img")

    app.include_router(boardgames.router)
    app.include_router(single_game.router)

    app.include_router(categories.router)
    app.include_router(designers.router)
    app.include_router(families.router)
    app.include_router(mechanics.router)

    app.include_router(search.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    return app
