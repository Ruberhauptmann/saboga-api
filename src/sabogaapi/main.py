from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db
from sabogaapi.logger import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Initialising database connection.")
    await init_db()
    yield


logger = configure_logger()
app = create_app(lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
