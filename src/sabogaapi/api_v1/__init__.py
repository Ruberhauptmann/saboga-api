"""Version 1 of the saboga API."""

from typing import Optional

import fastapi.openapi.utils as fu
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from sabogaapi.api_v1.routers import (
    boardgames,
    categories,
    designers,
    families,
    mechanics,
    search,
    single_game,
)

from .config import IMG_DIR, STATIC_DIR


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    extra_info: Optional[dict] = None


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
api_v1.include_router(single_game.router)

api_v1.include_router(categories.router)
api_v1.include_router(designers.router)
api_v1.include_router(families.router)
api_v1.include_router(mechanics.router)

api_v1.include_router(search.router)
api_v1.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
api_v1.mount("/img", StaticFiles(directory=IMG_DIR), name="img")


fu.validation_error_response_definition = ErrorResponse.model_json_schema()


@api_v1.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=str(exc.detail), status_code=exc.status_code
        ).dict(),
    )


@api_v1.exception_handler(RequestValidationError)  # Catches unexpected errors
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An internal server error occurred.", status_code=500
        ).dict(),
    )
