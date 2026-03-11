from pathlib import Path

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_uri: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://user:pass@localhost:5432/foobar"
    )
    bgg_username: str = ""
    bgg_password: str = ""
    echo_sql: bool = False
    img_dir: Path = Path("img")
    static_dir: Path = Path("static")


settings = Settings()

settings.img_dir.mkdir(exist_ok=True)
settings.static_dir.mkdir(exist_ok=True)
