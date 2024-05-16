from fastapi import FastAPI

from sabogaapi.api_v1.routers import boardgames, plays

api_v1 = FastAPI()


@api_v1.get("/hello")
def hello_world() -> str:
    return "Hello World!"


api_v1.include_router(boardgames.router)
api_v1.include_router(plays.router)
