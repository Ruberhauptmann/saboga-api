import os
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Mapping, Optional

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from sabogaapi.api_v1 import api_v1
from sabogaapi.api_v1.config import settings

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
    tags_metadata = [
        {
            "name": "v1",
            "description": "API version 1, check link on the right",
            "externalDocs": {
                "description": "sub-docs",
                "url": "https://saboga.tjarksievers.de/api/v1/docs",
            },
        }
    ]

    app = FastAPI(
        title="saboga",
        contact={
            "name": "Tjark Sievers",
            "url": "https://tjarksievers.de/about",
            "email": "tjarksievers@icloud.com",
        },
        openapi_tags=tags_metadata,
        license_info={
            "name": "MIT",
            "url": "https://github.com/Ruberhauptmann/saboga-api/blob/main/LICENSE.md",
        },
        lifespan=lifespan,
        root_path_in_servers=False,
    )

    app.include_router(api_v1, prefix="/v1")
    app.mount("/v1/static", StaticFiles(directory=settings.static_dir), name="static")
    app.mount("/v1/img", StaticFiles(directory=settings.img_dir), name="img")

    app.include_router(api_v1, prefix="/latest")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    return app
