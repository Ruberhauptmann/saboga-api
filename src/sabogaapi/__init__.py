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
    tags_metadata = [
        {
            "name": "v1",
            "description": "API version 1, check link on the right",
            "externalDocs": {
                "description": "sub-docs",
                "url": "https://api.saboga.tjarksievers.de/api/v1/docs",
            },
        }
    ]

    app = FastAPI(
        title="My Server",
        description=description,
        contact={
            "name": "Hello World Jr",
            "url": "https://api.saboga.tjarksievers.de",
            "email": "tjarksievers@icloud.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://github.com/Ruberhauptmann/saboga-api/blob/main/LICENSE.md",
        },
        openapi_tags=tags_metadata,
        lifespan=lifespan,
    )

    # app.mount("/", api_v1)
    app.mount("/v1", api_v1)
    app.mount("/latest", api_v1)

    origins = ["https://saboga.tjarksievers.de" "https://api.saboga.tjarksievers.de"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
