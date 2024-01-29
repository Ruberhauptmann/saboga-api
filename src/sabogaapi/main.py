from typing import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .routers import boardgames
from .database import engine


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://saboga.tjarksievers.de"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boardgames.router)
