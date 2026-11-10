import json
import unittest
from datetime import datetime, timezone

from nbafantasy.models.categories import Categories
from nbafantasy.website.league_json import LeagueJson
from tests.sample_league import SampleLeague


class LeagueJsonTest(unittest.TestCase):
    def setUp(self):
        self.data = SampleLeague.build()
        self.league = LeagueJson(self.data, "Test League", 2027,
                                now=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc))
        self.p = self.league.payload()

    def test_top_level_fields(self):
        self.assertEqual(self.p["schema_version"], LeagueJson.SCHEMA_VERSION)
        self.assertEqual(self.p["generated_at"], "2026-11-09T13:00:00+00:00")
        self.assertNotIn("my_team", self.p)  # the website gets "my team" from the login
        self.assertEqual(self.p["categories"], list(Categories.ALL))
        self.assertEqual([t["name"] for t in self.p["teams"]], self.data.teams)  # ESPN order
        self.assertEqual([r["team"] for r in self.p["season"]], self.data.teams)
        self.assertEqual(self.p["lower_is_better"], ["TO"])

    def test_weeks_rosters_and_season(self):
        self.assertEqual(len(self.p["weeks"]), len(self.data.weeks))
        self.assertFalse(self.p["weeks"][-1]["final"])
        self.assertEqual(self.p["weeks"][-1]["rows"][0]["result"], "Live")
        self.assertEqual(len(self.p["season"]), 8)
        self.assertEqual(len(self.p["season_completed"]), 8)
        first = self.p["season"][0]
        self.assertEqual(first["weeks"], 5)
        self.assertAlmostEqual(first["per_week"]["stats"]["PTS"], first["stats"]["PTS"] / 5, places=2)
        self.assertEqual(set(first["per_week"]["ranks"]), set(Categories.ALL))
        live_pts = sum(r["stats"]["PTS"] for r in self.p["weeks"][-1]["rows"])
        self.assertEqual(sum(r["stats"]["PTS"] for r in self.p["season"])
                         - sum(r["stats"]["PTS"] for r in self.p["season_completed"]), live_pts)
        self.assertEqual(set(self.p["rosters"]), set(self.data.teams))
        player = self.p["rosters"][self.data.teams[0]][0]
        self.assertEqual(player["slot"], "PG")
        self.assertIn("FG%", player["stats"])

    def test_player_weeks_are_summed_stats_with_shooting_percentages(self):
        source = self.data.rosters[self.data.teams[0]].in_lineup_order()[0]
        player = self.p["rosters"][self.data.teams[0]][0]
        self.assertTrue(source.weeks)
        self.assertEqual(list(player["weeks"]), [str(w) for w in sorted(source.weeks)])
        week, pw = sorted(source.weeks.items())[0]
        out = player["weeks"][str(week)]
        self.assertEqual(out["games"], pw.games)
        self.assertAlmostEqual(out["totals"]["PTS"], pw.totals["PTS"], places=1)
        self.assertAlmostEqual(out["totals"]["FG%"], pw.totals["FGM"] / pw.totals["FGA"], places=3)

    def test_payload_is_json_and_has_no_config_fields(self):
        text = json.dumps(self.p)
        for secret in ("espn_s2", "swid", "league_id", "sheet_id"):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
