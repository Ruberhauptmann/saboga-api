from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = create_app(lifespan=lifespan)
