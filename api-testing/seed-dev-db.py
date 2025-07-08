import asyncio
import datetime
import random
import re

from beanie import init_beanie
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient

from sabogaapi.api_v1.config import settings
from sabogaapi.api_v1.models import (
    Boardgame,
    Category,
    Designer,
    Family,
    Mechanic,
    RankHistory,
)
from sabogaapi.api_v1.statistics.volatility import calculate_volatility

fake = Faker()

NUM_GAMES = 20
HISTORY_DAYS = 30

CATEGORIES = [Category(name=fake.word(), bgg_id=i) for i in range(1, 10)]
MECHANICS = [Mechanic(name=fake.word(), bgg_id=i) for i in range(1, 10)]
FAMILIES = [Family(name=fake.word(), bgg_id=i) for i in range(1, 10)]
DESIGNERS = [Designer(name=fake.name(), bgg_id=i) for i in range(1, 10)]


def clean_title(text: str) -> str:
    return re.sub(r"[^\w\s]$", "", text.strip())


def generate_rank_history(
    bgg_id: int, days: int = 30
) -> tuple[list[RankHistory], dict]:
    trend_type = random.choice(["improving", "declining", "random"])
    base_rank = random.randint(100, 900)

    history = []
    today = datetime.datetime.now()

    for i in range(days):
        noise = random.gauss(0, 5)
        if trend_type == "improving":
            rank = max(1, base_rank - i * random.uniform(1, 5) + noise)
        elif trend_type == "declining":
            rank = min(1000, base_rank + i * random.uniform(1, 5) + noise)
        else:
            rank = min(1000, max(1, base_rank + random.gauss(0, 50)))

        # Simulate rating following rank: better rank → better rating
        geek_rating = round(10 - (rank / 1000 * 3.5) + random.uniform(-0.05, 0.05), 2)
        avg_rating = round(geek_rating + random.uniform(-0.1, 0.1), 2)

        history.append(
            RankHistory(
                date=today - datetime.timedelta(days=(days - i)),
                bgg_id=bgg_id,
                bgg_rank=int(rank),
                bgg_geek_rating=geek_rating,
                bgg_average_rating=avg_rating,
            )
        )

    latest = history[-1]
    latest_data = {
        "bgg_rank": latest.bgg_rank,
        "bgg_geek_rating": latest.bgg_geek_rating,
        "bgg_average_rating": latest.bgg_average_rating,
    }

    return history, latest_data


def generate_boardgame(bgg_id: int) -> tuple[Boardgame, list[RankHistory]]:
    rank_history, latest = generate_rank_history(bgg_id, HISTORY_DAYS)

    minplayers = random.randint(1, 4)
    maxplayers = random.randint(minplayers + 1, min(minplayers + 5, 10))

    minplay = random.randint(15, 60)
    maxplay = random.randint(minplay + 5, minplay + 90)

    title = clean_title(fake.sentence(nb_words=random.randint(2, 4)))

    rank_volatility, geek_rating_volatility, average_rating_volatility = (
        calculate_volatility(rank_history)
    )

    boardgame = Boardgame(
        bgg_id=bgg_id,
        bgg_rank=latest["bgg_rank"],
        bgg_geek_rating=latest["bgg_geek_rating"],
        bgg_average_rating=latest["bgg_average_rating"],
        bgg_rank_volatility=rank_volatility,
        bgg_geek_rating_volatility=geek_rating_volatility,
        bgg_average_rating_volatility=average_rating_volatility,
        name=title,
        description=fake.paragraph(nb_sentences=10),
        image_url=fake.image_url(),
        thumbnail_url=fake.image_url(),
        year_published=random.randint(1990, 2025),
        minplayers=minplayers,
        maxplayers=maxplayers,
        playingtime=random.randint(minplay, maxplay),
        minplaytime=minplay,
        maxplaytime=maxplay,
        categories=random.sample(CATEGORIES, k=random.randint(1, 3)),
        mechanics=random.sample(MECHANICS, k=random.randint(1, 2)),
        families=random.sample(FAMILIES, k=random.randint(0, 2)),
        designers=random.sample(DESIGNERS, k=random.randint(1, 2)),
    )

    return boardgame, rank_history


async def generate_data():
    client = AsyncIOMotorClient(f"{settings.mongodb_uri}")
    await init_beanie(
        database=client.get_database(), document_models=[Boardgame, RankHistory]
    )

    await Boardgame.delete_all()
    await RankHistory.delete_all()

    games = []
    history_entries = []

    for i in range(NUM_GAMES):
        game, history = generate_boardgame(1000 + i)
        games.append(game)
        history_entries.extend(history)

    await Boardgame.insert_many(games)
    await RankHistory.insert_many(history_entries)

    print(
        f"Inserted {NUM_GAMES} boardgames with {NUM_GAMES * HISTORY_DAYS} rank history entries."
    )


if __name__ == "__main__":
    asyncio.run(generate_data())
