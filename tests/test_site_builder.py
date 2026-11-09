import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from nbafantasy.website.league_json import LeagueJson
from nbafantasy.website.site_builder import SiteBuilder
from tests.sample_league import SampleLeague


class SiteBuilderTest(unittest.TestCase):
    def setUp(self):
        self.league = LeagueJson(SampleLeague.build(), "Test League", 2027,
                                 now=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc))

    def test_build_copies_web_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            web, out = os.path.join(d, "web"), os.path.join(d, "out")
            os.makedirs(os.path.join(web, "js"))
            for name, text in (("index.html", "<html></html>"), ("js/main.js", "//"), (".hidden", "x")):
                with open(os.path.join(web, name), "w") as f:
                    f.write(text)
            self.assertEqual(SiteBuilder(web, out).build(self.league), out)
            self.assertEqual(sorted(os.listdir(out)), ["index.html", "js", "league.json"])
            self.assertTrue(os.path.exists(os.path.join(out, "js", "main.js")))
            with open(os.path.join(out, "league.json")) as f:
                self.assertEqual(json.load(f)["title"], "Test League")

    def test_rebuild_removes_files_no_longer_in_web(self):
        with tempfile.TemporaryDirectory() as d:
            web, out = os.path.join(d, "web"), os.path.join(d, "out")
            os.makedirs(web)
            with open(os.path.join(web, "old.js"), "w") as f:
                f.write("//")
            SiteBuilder(web, out).build(self.league)
            os.remove(os.path.join(web, "old.js"))
            SiteBuilder(web, out).build(self.league)
            self.assertEqual(os.listdir(out), ["league.json"])


if __name__ == "__main__":
    unittest.main()
