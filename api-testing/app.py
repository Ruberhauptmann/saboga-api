from contextlib import asynccontextmanager

from fastapi import FastAPI

from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = create_app(lifespan=lifespan)
