from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sabogaapi import create_app
from sabogaapi.database import sessionmanager
from sabogaapi.logger import configure_logger
from sabogaapi.metrics import instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Got app %s", app.title)
    logger.info("Initialising database connection.")
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


logger = configure_logger()
app = create_app(lifespan=lifespan)
instrumentator.instrument(app).expose(app)
