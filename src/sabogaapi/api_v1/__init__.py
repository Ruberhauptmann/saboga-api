from fastapi import FastAPI

from sabogaapi.api_v1.routers import boardgames

api_v1 = FastAPI()

api_v1.include_router(boardgames.router)
