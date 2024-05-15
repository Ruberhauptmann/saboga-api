from fastapi import FastAPI

from sabogaapi.api_v1.database import init_db
from sabogaapi.api_v1.routers import boardgames, plays

api_v1 = FastAPI()

api_v1.include_router(boardgames.router)
api_v1.include_router(plays.router)
