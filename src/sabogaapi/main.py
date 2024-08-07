import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Initialising database connection.")
    await init_db()
    yield


logger = logging.getLogger(__name__)
app = create_app(lifespan=lifespan)
