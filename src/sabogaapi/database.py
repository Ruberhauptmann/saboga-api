import os

from sqlmodel import create_engine

db_driver = f'{os.getenv("DB_DRIVER", "sqlite")}://'

if db_driver == "sqlite://":
    connection_string = db_driver
else:
    connection_string = (
        f"{db_driver}"
        f'{os.getenv("MARIADB_USER")}'
        f':{os.getenv("MARIADB_PASSWORD")}@{os.getenv("DB_URL")}:{os.getenv("DB_PORT")}'
        f'/{os.getenv("MARIADB_DATABASE")}'
    )

engine = create_engine(connection_string)
