from sabogaapi import create_app
from sabogaapi.api_v1.database import init_db

app = create_app()


@app.on_event("startup")
async def startup_db_client():
    await init_db()
