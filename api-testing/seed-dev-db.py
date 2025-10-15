import asyncio
import datetime
import random
import re

from faker import Faker
from PIL import Image, ImageDraw, ImageFont

from sabogaapi import models, schemas
from sabogaapi.database import Base, sessionmanager
from sabogaapi.statistics.clusters import (
    construct_boardgame_network,
    construct_category_network,
    construct_designer_network,
    construct_family_network,
    construct_mechanic_network,
    graph_to_dict,
)
from sabogaapi.statistics.trending import calculate_trends
from sabogaapi.statistics.volatility import calculate_volatility

fake = Faker()

NUM_GAMES = 10
NUM_DESIGNERS = 4
HISTORY_DAYS = 35


# --- Helpers ---
def clean_title(text: str) -> str:
    return re.sub(r"[^\w\s]$", "", text.strip())


def generate_rank_history(days: int = 30):
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

        geek_rating = round(10 - (rank / 1000 * 3.5) + random.uniform(-0.05, 0.05), 2)
        avg_rating = round(geek_rating + random.uniform(-0.1, 0.1), 2)

        history.append(
            models.RankHistory(
                date=today - datetime.timedelta(days=(days - i - 1)),
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
    bg_color = tuple(random.randint(100, 255) for _ in range(3))
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", size=int(min(size) / 4))
    except OSError:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)

    draw.text(position, text, fill="black", font=font)
    img.save(filepath)


def generate_boardgame(bgg_id, designers, categories, families, mechanics):
    rank_history, latest = generate_rank_history(HISTORY_DAYS)

    minplayers = random.randint(1, 4)
    maxplayers = random.randint(minplayers + 1, min(minplayers + 5, 10))

    minplay = random.randint(15, 60)
    maxplay = random.randint(minplay + 5, minplay + 90)

    title = clean_title(fake.sentence(nb_words=random.randint(2, 4)))

    rank_volatility, geek_rating_volatility, average_rating_volatility = (
        calculate_volatility(
            [
                schemas.RankHistory.model_validate(entry.__dict__)
                for entry in rank_history
            ]
        )
    )

    rank_trend, geek_rating_trend, average_rating_trend, mean_trend = calculate_trends(
        [schemas.RankHistory.model_validate(entry.__dict__) for entry in rank_history]
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
        mean_trend=mean_trend,
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
        bgg_rank_history=rank_history,
        categories=random.sample(categories, k=random.randint(1, 3)),
        mechanics=random.sample(mechanics, k=random.randint(1, 2)),
        families=random.sample(families, k=random.randint(1, 2)),
        designers=random.sample(designers, k=random.randint(1, 2)),
    )

    return boardgame, rank_history


async def generate_data():
    async with sessionmanager.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmanager.session() as session:
        designers = [
            models.Designer(name=fake.name(), bgg_id=i) for i in range(1, NUM_DESIGNERS)
        ]
        categories = [models.Category(name=fake.word(), bgg_id=i) for i in range(1, 20)]
        families = [models.Family(name=fake.word(), bgg_id=i) for i in range(1, 20)]
        mechanics = [models.Mechanic(name=fake.word(), bgg_id=i) for i in range(1, 20)]

        session.add_all(designers + categories + families + mechanics)
        await session.commit()

        games = []
        history_entries = []

        for i in range(NUM_GAMES):
            game, history = generate_boardgame(
                bgg_id=1000 + i,
                designers=designers,
                families=families,
                mechanics=mechanics,
                categories=categories,
            )
            games.append(game)
            history_entries.extend(history)

        session.add_all(games + history_entries)
        await session.commit()

        # networks (if you want to persist those too)
        category_graph = await construct_category_network()
        session.add(models.CategoryNetwork(**graph_to_dict(category_graph)))

        designer_graph = await construct_designer_network()
        session.add(models.DesignerNetwork(**graph_to_dict(designer_graph)))

        family_graph = await construct_family_network()
        session.add(models.FamilyNetwork(**graph_to_dict(family_graph)))

        mechanic_graph = await construct_mechanic_network()
        session.add(models.MechanicNetwork(**graph_to_dict(mechanic_graph)))

        boardgame_graph = await construct_boardgame_network()
        session.add(models.BoardgameNetwork(**graph_to_dict(boardgame_graph)))

        await session.commit()

    print(
        f"Inserted {NUM_GAMES} boardgames with {NUM_GAMES * HISTORY_DAYS} rank history entries."
    )


if __name__ == "__main__":
    asyncio.run(generate_data())
