import os
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Mapping

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sabogaapi.api_v1 import api_v1

SECRET = os.getenv("FASTAPI-USERS-SECRET")


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]]
    | Callable[[FastAPI], AbstractAsyncContextManager[Mapping[str, Any]]]
    | None
) -> FastAPI:
    description = """
    Boardgame storage
    """

    app = FastAPI(
        title="Saboga",
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
        lifespan=lifespan,
        root_path_in_servers=False,
    )

    app.mount("/v1", api_v1)
    app.mount("/latest", api_v1)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
