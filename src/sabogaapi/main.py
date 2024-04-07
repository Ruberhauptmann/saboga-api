from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import boardgames, plays

app = FastAPI()

origins = ["https://saboga.tjarksievers.de" "https://api.saboga.tjarksievers.de"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boardgames.router)
app.include_router(plays.router)
