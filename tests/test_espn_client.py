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


class EspnClientPlayerWeeksTest(unittest.TestCase):
    """Game-by-game player stats summed into fantasy weeks."""

    PERIODS = {1: ["1", "2", "3"], 2: ["4", "5"], 3: ["6"]}

    @staticmethod
    def game(**stats):
        return {"total": {"GP": 1, **stats}}

    def test_games_are_summed_by_week(self):
        stats = {"2026_total": {"avg": {"PTS": 20}}, "1": self.game(PTS=20, MIN=30), "3": self.game(PTS=10, MIN=20),
                 "5": self.game(PTS=7, MIN=12, TO=2)}
        weeks = EspnClient.group_games(stats, self.PERIODS)
        self.assertEqual(sorted(weeks), [1, 2])  # no game in week 3
        self.assertEqual(weeks[1].games, 2)
        self.assertEqual(weeks[1].totals["PTS"], 30)
        self.assertEqual(weeks[1].totals["MIN"], 50)
        self.assertEqual(weeks[2].totals["TO"], 2)
        self.assertEqual(weeks[2].totals["REB"], 0)

    def test_a_did_not_play_entry_is_not_a_game(self):
        weeks = EspnClient.group_games({"4": {"total": {"GP": 0, "MIN": 0}}, "6": {"total": None}}, self.PERIODS)
        self.assertEqual(weeks, {})

    def league(self, player_info):
        p = SimpleNamespace(playerId=7)
        return SimpleNamespace(teams=[SimpleNamespace(roster=[p])], matchup_ids={1: ["1"]}, player_info=player_info)

    def test_one_request_for_every_player(self):
        asked = []

        def info(playerId):
            asked.append(playerId)
            return SimpleNamespace(playerId=7, stats={"1": self.game(PTS=12)})
        weeks = EspnClient(Config(league_id=1))._player_weeks(self.league(info), current=1)
        self.assertEqual(asked, [[7]])
        self.assertEqual(weeks[7][1].totals["PTS"], 12)

    def test_espn_failing_gives_no_weeks_instead_of_failing_the_update(self):
        def info(playerId):
            raise RuntimeError("HTTP 500")
        weeks = EspnClient(Config(league_id=1))._player_weeks(self.league(info), current=1)
        self.assertEqual(weeks, {})


if __name__ == "__main__":
    unittest.main()
