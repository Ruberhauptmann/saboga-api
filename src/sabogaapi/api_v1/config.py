from pathlib import Path

from pydantic import MongoDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: MongoDsn = MongoDsn("mongodb://localhost")
    img_dir: Path = Path("img")
    static_dir: Path = Path("static")


settings = Settings()

settings.img_dir.mkdir(exist_ok=True)
settings.static_dir.mkdir(exist_ok=True)
