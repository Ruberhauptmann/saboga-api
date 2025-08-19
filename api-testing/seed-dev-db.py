import asyncio
import datetime
import random
import re

from beanie import init_beanie
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont

from sabogaapi import models, schemas
from sabogaapi.config import settings
from sabogaapi.scraper._fill_in_data import construct_designer_network, graph_to_dict
from sabogaapi.statistics.trending import calculate_trends
from sabogaapi.statistics.volatility import calculate_volatility

fake = Faker()

NUM_GAMES = 20
HISTORY_DAYS = 30

CATEGORIES = [models.Category(name=fake.word(), bgg_id=i) for i in range(1, 10)]
MECHANICS = [models.Mechanic(name=fake.word(), bgg_id=i) for i in range(1, 10)]
FAMILIES = [models.Family(name=fake.word(), bgg_id=i) for i in range(1, 10)]


def clean_title(text: str) -> str:
    return re.sub(r"[^\w\s]$", "", text.strip())


def generate_rank_history(
    bgg_id: int,
    days: int = 30,
) -> tuple[list[models.RankHistory], dict]:
    trend_type = random.choice(["improving", "declining", "random"])
    base_rank = random.randint(100, 900)

    history = []
    today = datetime.datetime.now(datetime.UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

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
            models.RankHistory(
                date=today - datetime.timedelta(days=(days - i - 1)),
                bgg_id=bgg_id,
                bgg_rank=int(rank),
                bgg_geek_rating=geek_rating,
                bgg_average_rating=avg_rating,
            ),
        )

    latest = history[-1]
    latest_data = {
        "bgg_rank": latest.bgg_rank,
        "bgg_geek_rating": latest.bgg_geek_rating,
        "bgg_average_rating": latest.bgg_average_rating,
    }

    return history, latest_data


def generate_image_with_text(filepath: str, text: str, size: tuple[int, int]):
    # Random background color
    bg_color = tuple(random.randint(100, 255) for _ in range(3))
    # Create image
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load a default font
    try:
        font = ImageFont.truetype("arial.ttf", size=int(min(size) / 4))
    except OSError:
        font = ImageFont.load_default()

    # Center the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)

    draw.text(position, text, fill="black", font=font)
    img.save(filepath)


def generate_boardgame(
    bgg_id: int,
    designers: list[models.Designer],
) -> tuple[models.Boardgame, list[models.RankHistory]]:
    rank_history, latest = generate_rank_history(bgg_id, HISTORY_DAYS)

    minplayers = random.randint(1, 4)
    maxplayers = random.randint(minplayers + 1, min(minplayers + 5, 10))

    minplay = random.randint(15, 60)
    maxplay = random.randint(minplay + 5, minplay + 90)

    title = clean_title(fake.sentence(nb_words=random.randint(2, 4)))

    rank_volatility, geek_rating_volatility, average_rating_volatility = (
        calculate_volatility(
            [schemas.RankHistory(**entry.model_dump()) for entry in rank_history]
        )
    )

    rank_trend, geek_rating_trend, average_rating_trend = calculate_trends(
        [schemas.RankHistory(**entry.model_dump()) for entry in rank_history]
    )

    if random.choice([True, False]):
        main_size = (500, 500)
        thumb_size = (100, 100)
    else:
        main_size = (600, 400)
        thumb_size = (120, 80)

    main_image_path = f"{bgg_id}.png"
    thumb_image_path = f"{bgg_id}-thumbnail.png"

    generate_image_with_text(f"img/{main_image_path}", str(bgg_id), main_size)
    generate_image_with_text(f"img/{thumb_image_path}", str(bgg_id), thumb_size)

    boardgame = models.Boardgame(
        bgg_id=bgg_id,
        bgg_rank=latest["bgg_rank"],
        bgg_geek_rating=latest["bgg_geek_rating"],
        bgg_average_rating=latest["bgg_average_rating"],
        bgg_rank_volatility=rank_volatility,
        bgg_rank_trend=rank_trend,
        bgg_geek_rating_volatility=geek_rating_volatility,
        bgg_geek_rating_trend=geek_rating_trend,
        bgg_average_rating_volatility=average_rating_volatility,
        bgg_average_rating_trend=average_rating_trend,
        name=title,
        description=fake.paragraph(nb_sentences=10),
        image_url=f"/img/{main_image_path}",
        thumbnail_url=f"/img/{thumb_image_path}",
        year_published=random.randint(1990, 2025),
        minplayers=minplayers,
        maxplayers=maxplayers,
        playingtime=random.randint(minplay, maxplay),
        minplaytime=minplay,
        maxplaytime=maxplay,
        categories=random.sample(CATEGORIES, k=random.randint(1, 3)),
        mechanics=random.sample(MECHANICS, k=random.randint(1, 2)),
        families=random.sample(FAMILIES, k=random.randint(0, 2)),
        designers=random.sample(designers, k=random.randint(1, 4)),  # type: ignore
    )

    return boardgame, rank_history


async def generate_data():
    client = AsyncIOMotorClient(f"{settings.mongodb_uri}")
    await init_beanie(
        database=client.get_database(),
        document_models=[
            models.Boardgame,
            models.RankHistory,
            models.Designer,
            models.DesignerNetwork,
        ],
    )

    await models.Boardgame.delete_all()
    await models.RankHistory.delete_all()
    await models.Designer.delete_all()

    designers = [models.Designer(name=fake.name(), bgg_id=i) for i in range(1, 25)]
    await models.Designer.insert_many(designers)
    designers = await models.Designer.find_all(fetch_links=True).to_list()

    games = []
    history_entries = []

    for i in range(NUM_GAMES):
        game, history = generate_boardgame(1000 + i, designers)
        games.append(game)
        history_entries.extend(history)

    await models.Boardgame.insert_many(games)
    await models.RankHistory.insert_many(history_entries)

    graph = await construct_designer_network()
    await models.DesignerNetwork.delete_all()
    graph_db = models.DesignerNetwork(**graph_to_dict(graph))
    await graph_db.insert()

    print(
        f"Inserted {NUM_GAMES} boardgames with {NUM_GAMES * HISTORY_DAYS} rank history entries.",
    )


if __name__ == "__main__":
    asyncio.run(generate_data())
