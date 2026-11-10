import json
import os
import tempfile
import unittest

from nbafantasy.common.sync_error import SyncError
from nbafantasy.config.config import Config


class ConfigTest(unittest.TestCase):
    ENV = {"LEAGUE_ID": "123", "ESPN_S2": " s2 ", "ESPN_SWID": "{ABC}",
           "MY_TEAM_NAME": "IRen ", "PUBLISH_SITE": "true"}

    def test_reads_config_json_when_it_exists(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.json")
            with open(path, "w") as f:
                json.dump({"league_id": 7, "season_year": 2026, "publish_site": True}, f)
            c = Config.load(path, env=self.ENV)  # the file wins over the environment
        self.assertEqual((c.league_id, c.season_year, c.publish_site), (7, 2026, True))
        self.assertFalse(c.has_cookies)

    def test_falls_back_to_environment_variables(self):
        c = Config.load("/no/such/config.json", env=self.ENV)
        self.assertEqual((c.league_id, c.season_year), (123, None))  # None: ask ESPN
        self.assertEqual((c.espn_s2, c.swid, c.my_team_name), ("s2", "{ABC}", "IRen"))
        self.assertTrue(c.publish_site)
        self.assertTrue(c.has_cookies)
        self.assertEqual(c.sheet_title, Config.sheet_title)  # empty SHEET_TITLE keeps the default

    def test_publish_site_is_off_unless_set_to_true(self):
        for value in ("", "false", "0", "no"):
            env = dict(self.ENV, PUBLISH_SITE=value)
            self.assertFalse(Config.load("/no/such/config.json", env=env).publish_site, value)

    def test_season_year_is_optional_but_still_honored(self):
        self.assertEqual(Config.load("/no/such/config.json", env=dict(self.ENV, SEASON_YEAR="2026")).season_year, 2026)
        self.assertIsNone(Config.from_dict({"league_id": 1}).season_year)

    def test_missing_league_id_is_a_clear_error(self):
        with self.assertRaises(SyncError) as ctx:
            Config.load("/no/such/config.json", env={"ESPN_S2": "x"})
        self.assertIn("LEAGUE_ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
