import unittest
from types import SimpleNamespace

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


class EspnClientDraftOrderTest(unittest.TestCase):
    """The first-round picks give the draft order; anything odd gives none."""

    @staticmethod
    def pick(team_id, round_num, round_pick):
        return SimpleNamespace(team=SimpleNamespace(team_id=team_id), round_num=round_num, round_pick=round_pick)

    NAMES = {1: "A", 2: "B", 3: "C"}

    def test_first_round_picks_in_pick_order(self):
        league = SimpleNamespace(draft=[self.pick(2, 1, 1), self.pick(3, 1, 2), self.pick(1, 1, 3),
                                        self.pick(1, 2, 1), self.pick(3, 2, 2), self.pick(2, 2, 3)])
        self.assertEqual(EspnClient.draft_order(league, self.NAMES), ["B", "C", "A"])

    def test_no_draft_yet(self):
        self.assertEqual(EspnClient.draft_order(SimpleNamespace(draft=[]), self.NAMES), [])

    def test_a_team_twice_in_round_one_gives_no_order(self):
        league = SimpleNamespace(draft=[self.pick(2, 1, 1), self.pick(2, 1, 2), self.pick(1, 1, 3)])
        self.assertEqual(EspnClient.draft_order(league, self.NAMES), [])


if __name__ == "__main__":
    unittest.main()
