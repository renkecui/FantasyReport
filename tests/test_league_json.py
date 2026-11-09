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
        self.assertEqual(self.p["my_team"], self.data.my_team)
        self.assertEqual(self.p["categories"], list(Categories.ALL))
        self.assertEqual(self.p["teams"][0]["name"], self.data.my_team)
        self.assertEqual(self.p["lower_is_better"], ["TO"])

    def test_weeks_rosters_and_season(self):
        self.assertEqual(len(self.p["weeks"]), len(self.data.weeks))
        self.assertFalse(self.p["weeks"][-1]["final"])
        self.assertEqual(self.p["weeks"][-1]["rows"][0]["result"], "Live")
        self.assertEqual(len(self.p["season"]), 8)
        self.assertEqual(set(self.p["rosters"]), set(self.data.teams))
        player = self.p["rosters"][self.data.my_team][0]
        self.assertEqual(player["slot"], "PG")
        self.assertIn("FG%", player["stats"])

    def test_payload_is_json_and_has_no_config_fields(self):
        text = json.dumps(self.p)
        for secret in ("espn_s2", "swid", "league_id", "sheet_id"):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
