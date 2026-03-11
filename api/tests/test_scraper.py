from io import StringIO
from unittest.mock import patch

import pandas as pd
from django.core.management import call_command
from django.test import TestCase

from api import models
from api.scraper._update import insert_games


class ScraperInsertTests(TestCase):
    def setUp(self) -> None:
        # ensure clean database
        models.Boardgame.objects.all().delete()
        models.RankHistory.objects.all().delete()

    def test_insert_and_update(self):
        data = {
            "id": [1, 2],
            "rank": [1, 2],
            "bayesaverage": [8.0, 7.5],
            "average": [7.8, 7.0],
            "yearpublished": [2020, 2019],
            "name": ["Game One", "Game Two"],
        }
        df = pd.DataFrame(data)

        new_games, updated = insert_games(df)
        self.assertEqual(len(new_games), 2)
        self.assertEqual(updated, 0)

        # second run modifies the rank of the first game
        df.loc[0, "rank"] = 5
        new_games2, updated2 = insert_games(df)
        self.assertEqual(len(new_games2), 0)
        self.assertEqual(updated2, 2)

        game1 = models.Boardgame.objects.get(bgg_id=1)
        self.assertEqual(game1.bgg_rank, 5)
        history = game1.bgg_rank_history.order_by("date").all()
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].bgg_rank, 1)
        self.assertEqual(history[1].bgg_rank, 5)

        # statistics fields should be populated (not None)
        self.assertIsNotNone(game1.bgg_rank_volatility)
        self.assertIsNotNone(game1.bgg_rank_trend)


class UpdateCommandTests(TestCase):
    @patch("api.scraper._update.download_zip")
    def test_update_command_outputs_counts(self, mock_download):
        data = {
            "id": [42],
            "rank": [10],
            "bayesaverage": [6.0],
            "average": [6.5],
            "yearpublished": [2021],
            "name": ["Mock"],
        }
        mock_download.return_value = pd.DataFrame(data)

        out = StringIO()
        call_command("update", stdout=out)
        output = out.getvalue()
        self.assertIn("Inserted 1 new boardgames", output)
        self.assertIn("Updated 0 existing boardgames", output)
