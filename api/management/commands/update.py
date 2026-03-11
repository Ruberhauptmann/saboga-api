from django.core.management.base import BaseCommand
import logging

from api.scraper._update import download_zip, insert_games

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates the boardgame ranks and ratings."

    def handle(self, *args, **options):
        logger.info("Starting scrape process.")
        games_df = download_zip()

        new_games, updated_games = insert_games(games_df)

        logger.info("Inserted %s new boardgames.", len(new_games))
        logger.info("Updated %s existing boardgames.", updated_games)
