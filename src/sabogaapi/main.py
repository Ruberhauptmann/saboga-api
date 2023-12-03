from fastapi import FastAPI

from .routers import boardgames

app = FastAPI()

app.include_router(boardgames.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"msg": "Hello World"}
