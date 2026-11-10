import unittest

from nbafantasy.common.sync_error import SyncError
from nbafantasy.config.config import Config
from nbafantasy.espn.espn_client import EspnClient


class EspnClientSeasonTest(unittest.TestCase):
    def test_asks_espn_when_season_year_is_not_set(self):
        client = EspnClient(Config(league_id=1), current_season=lambda: 2027)
        self.assertEqual(client.season_year(), 2027)

    def test_a_set_season_year_wins_and_espn_is_not_asked(self):
        def never():
            raise AssertionError("ESPN should not be asked")
        self.assertEqual(EspnClient(Config(league_id=1, season_year=2025), current_season=never).season_year(), 2025)

    def test_a_missing_answer_from_espn_is_a_clear_error(self):
        for answer in (None, "2027", 0):
            with self.assertRaises(SyncError):
                EspnClient(Config(league_id=1), current_season=lambda a=answer: a).season_year()


if __name__ == "__main__":
    unittest.main()
