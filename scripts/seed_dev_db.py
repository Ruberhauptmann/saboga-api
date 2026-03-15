#!/usr/bin/env python3
"""Utility to populate the development database with fake data.

This script was originally written for the async SQLAlchemy backend and has
been rewritten for the current Django + DRF setup.  It can be executed from
inside the project root (the DJANGO_SETTINGS_MODULE is configured below),
or via ``python manage.py runscript seed_dev_db`` once ``django-extensions``
is installed.

The generated data mirrors the previous version: a handful of designers,
categories, mechanics and families plus a small number of boardgames along
with a rank history for each game.  Image files are dropped into
``api-testing/img`` so that the frontend can serve them from ``/img/``.
"""

import os
import datetime
import random
import re

from faker import Faker
from PIL import Image, ImageDraw, ImageFont
from django.core.files import File

from api import models
from api.statistics import calculate_trends, calculate_volatility

# set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saboga_project.settings")
import django

django.setup()


fake = Faker()

NUM_GAMES = 20
NUM_DESIGNERS = 4
HISTORY_DAYS = 35


# --- Helpers ----------------------------------------------------------------


def clean_title(text: str) -> str:
    """Drop trailing punctuation and trim whitespace."""
    return re.sub(r"[^\w\s]$", "", text.strip())


def generate_rank_history(days: int = 30):
    """Return a list of dicts describing rank data and the final values.

    The old version returned unsaved ``RankHistory`` model instances; the
    Django script keeps to plain dictionaries so that the calculations in
    :mod:`api.statistics` still work and the ORM objects are created later
    once the associated ``Boardgame`` exists.
    """
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
            {
                "date": today - datetime.timedelta(days=(days - i - 1)),
                "bgg_rank": int(rank),
                "bgg_geek_rating": geek_rating,
                "bgg_average_rating": avg_rating,
            }
        )

    latest = history[-1]
    latest_data = {
        "bgg_rank": latest["bgg_rank"],
        "bgg_geek_rating": latest["bgg_geek_rating"],
        "bgg_average_rating": latest["bgg_average_rating"],
    }

    return history, latest_data


# the image helper remains unchanged


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
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath)


def generate_boardgame(bgg_id, designers, categories, families, mechanics):
    """Return an unsaved ``Boardgame`` instance plus its rank history dicts."""
    rank_history, latest = generate_rank_history(HISTORY_DAYS)

    minplayers = random.randint(1, 4)
    maxplayers = random.randint(minplayers + 1, min(minplayers + 5, 10))

    minplay = random.randint(15, 60)
    maxplay = random.randint(minplay + 5, minplay + 90)

    title = clean_title(fake.sentence(nb_words=random.randint(2, 4)))

    rank_volatility, geek_rating_volatility, average_rating_volatility = (
        calculate_volatility(rank_history)
    )

    rank_trend, geek_rating_trend, average_rating_trend, mean_trend = calculate_trends(
        rank_history
    )

    if random.choice([True, False]):
        main_size = (500, 500)
        thumb_size = (100, 100)
    else:
        main_size = (600, 400)
        thumb_size = (120, 80)

    main_image_path = f"{bgg_id}.png"
    thumb_image_path = f"{bgg_id}-thumbnail.png"

    generate_image_with_text(
        f"api-testing/img/{main_image_path}", str(bgg_id), main_size
    )
    generate_image_with_text(
        f"api-testing/img/{thumb_image_path}", str(bgg_id), thumb_size
    )

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
        year_published=random.randint(1990, 2025),
        minplayers=minplayers,
        maxplayers=maxplayers,
        playingtime=random.randint(minplay, maxplay),
        minplaytime=minplay,
        maxplaytime=maxplay,
    )

    with open(f"api-testing/img/{main_image_path}", "rb") as main_img_file:
        boardgame.image.save(main_image_path, File(main_img_file), save=False)
    with open(f"api-testing/img/{thumb_image_path}", "rb") as thumb_img_file:
        boardgame.thumbnail.save(thumb_image_path, File(thumb_img_file), save=False)

    return boardgame, rank_history


def generate_data():
    """Create or replace the development data set.

    The previous async implementation dropped / recreated the schema; here we
    simply flush the tables to keep migrations intact.  After the data has been
    inserted we optionally call a placeholder for graph building if such a
    service exists in the Django codebase.
    """
    # wipe out old rows
    models.RankHistory.objects.all().delete()
    models.Boardgame.objects.all().delete()
    models.Category.objects.all().delete()
    models.Designer.objects.all().delete()
    models.Family.objects.all().delete()
    models.Mechanic.objects.all().delete()

    # create static lookup tables
    designers = [
        models.Designer(name=fake.name(), bgg_id=i) for i in range(1, NUM_DESIGNERS)
    ]
    categories = [models.Category(name=fake.word(), bgg_id=i) for i in range(1, 20)]
    families = [models.Family(name=fake.word(), bgg_id=i) for i in range(1, 20)]
    mechanics = [models.Mechanic(name=fake.word(), bgg_id=i) for i in range(1, 20)]

    models.Designer.objects.bulk_create(designers)
    models.Category.objects.bulk_create(categories)
    models.Family.objects.bulk_create(families)
    models.Mechanic.objects.bulk_create(mechanics)

    # refresh lists from DB because bulk_create doesn't set PKs by default
    designers = list(models.Designer.objects.all())
    categories = list(models.Category.objects.all())
    families = list(models.Family.objects.all())
    mechanics = list(models.Mechanic.objects.all())

    for i in range(NUM_GAMES):
        game, history = generate_boardgame(
            bgg_id=1000 + i,
            designers=designers,
            families=families,
            mechanics=mechanics,
            categories=categories,
        )
        game.save()
        # assign many-to-many relationships
        game.designers.set(random.sample(designers, k=random.randint(1, 2)))
        game.categories.set(random.sample(categories, k=random.randint(1, 3)))
        game.mechanics.set(random.sample(mechanics, k=random.randint(1, 2)))
        game.families.set(random.sample(families, k=random.randint(1, 2)))

        # create rank history entries now that the boardgame has a PK
        rh_objects = [models.RankHistory(boardgame=game, **entry) for entry in history]
        models.RankHistory.objects.bulk_create(rh_objects)

    # placeholder for graph rebuild; implement if you have equivalent service
    try:
        from api.services import graph_service

        graph_service.build_and_save_all()
    except ImportError:
        pass


def run():
    generate_data()
