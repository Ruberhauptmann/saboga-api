from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db
from sabogaapi.logger import configure_logger
from sabogaapi.metrics import instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # pragma: no cover
    logger.info("Initialising database connection.")
    await init_db()
    yield


logger = configure_logger()
app = create_app(lifespan=lifespan)
instrumentator.instrument(app).expose(app)
