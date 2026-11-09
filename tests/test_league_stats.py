import unittest

from nbafantasy.models.categories import Categories
from nbafantasy.models.league_data import LeagueData
from nbafantasy.models.matchup_row import MatchupRow
from nbafantasy.models.week import Week
from nbafantasy.stats.league_stats import LeagueStats
from tests.sample_league import SampleLeague


class LeagueStatsTest(unittest.TestCase):
    @staticmethod
    def stats(**over):
        """Default week stats; FG= and FT= set FG% and FT%."""
        base = {"FG%": 0.45, "FT%": 0.80, "3PM": 50, "REB": 200, "AST": 100,
                "STL": 30, "BLK": 20, "TO": 60, "PTS": 500}
        base.update({k + "%" if k in ("FG", "FT") else k: v for k, v in over.items()})
        return base

    @classmethod
    def row(cls, team, opp, result, w=5, l=4, t=0, **st):
        return MatchupRow(team, opp, w, l, t, result, cls.stats(**st))

    def setUp(self):
        # Week 1 final, week 2 live. Team C has a bye in week 2.
        w1 = Week(1, True, [
            self.row("A", "B", "W", 6, 3, 0, PTS=600, TO=50, FG=0.50),
            self.row("B", "A", "L", 3, 6, 0, PTS=550, TO=70, FG=0.40),
            self.row("C", "D", "T", 4, 4, 1, PTS=550, TO=50, FG=0.45),
            self.row("D", "C", "T", 4, 4, 1, PTS=500, TO=60, FG=0.45),
        ])
        w2 = Week(2, False, [
            self.row("A", "D", "Live", 2, 7, 0, PTS=400, FG=0.40),
            self.row("D", "A", "Live", 7, 2, 0, PTS=700, FG=0.48),
        ])
        self.data = LeagueData(teams=["A", "B", "C", "D"], weeks=[w1, w2], rosters={}, my_team="C")
        self.s = LeagueStats(self.data)

    def weekly(self, week, team):
        return next(w for w in self.s.weekly if w.week == week and w.row.team == team)

    def season(self, team):
        return next(r for r in self.s.season if r.team == team)

    def test_weekly_ranks_only_compare_the_same_week(self):
        self.assertEqual(self.weekly(1, "A").ranks["PTS"], 1)
        self.assertEqual(self.weekly(1, "B").ranks["PTS"], 2)   # tie with C
        self.assertEqual(self.weekly(1, "C").ranks["PTS"], 2)
        self.assertEqual(self.weekly(1, "D").ranks["PTS"], 4)
        self.assertEqual(self.weekly(2, "A").ranks["PTS"], 2)
        self.assertEqual(self.weekly(2, "D").ranks["PTS"], 1)

    def test_turnovers_fewer_is_better(self):
        self.assertEqual(self.weekly(1, "A").ranks["TO"], 1)
        self.assertEqual(self.weekly(1, "C").ranks["TO"], 1)
        self.assertEqual(self.weekly(1, "D").ranks["TO"], 3)
        self.assertEqual(self.weekly(1, "B").ranks["TO"], 4)

    def test_avg_and_overall_rank(self):
        a = self.weekly(1, "A")
        self.assertAlmostEqual(a.avg_rank, sum(a.ranks.values()) / len(Categories.ALL))
        overall = {t: self.weekly(1, t).overall_rank for t in "ABCD"}
        self.assertEqual(overall["A"], 1)
        self.assertEqual(sorted(overall.values())[0], 1)
        self.assertEqual(self.weekly(2, "D").overall_rank, 1)

    def test_record_ignores_live_weeks(self):
        a = self.season("A")
        self.assertEqual((a.wins, a.losses, a.ties), (1, 0, 0))
        self.assertEqual(a.record, "1-0-0")
        self.assertEqual(self.season("C").record, "0-0-1")

    def test_category_record_and_counting_stats_include_live_week(self):
        a = self.season("A")
        self.assertEqual((a.cat_wins, a.cat_losses, a.cat_ties), (8, 10, 0))
        self.assertEqual(a.stats["PTS"], 1000)

    def test_percentages_are_average_of_weeks(self):
        self.assertAlmostEqual(self.season("A").stats["FG%"], 0.45)
        self.assertAlmostEqual(self.season("D").stats["FG%"], (0.45 + 0.48) / 2)

    def test_league_ranks(self):
        pts = {t: self.season(t).ranks["PTS"] for t in "ABCD"}
        self.assertEqual(pts, {"D": 1, "A": 2, "B": 3, "C": 3})
        to = {t: self.season(t).ranks["TO"] for t in "ABCD"}
        self.assertEqual(to, {"C": 1, "B": 2, "D": 4, "A": 3})

    def test_completed_season_leaves_out_the_live_week(self):
        a = next(r for r in self.s.season_completed if r.team == "A")
        self.assertEqual(a.record, "1-0-0")
        self.assertEqual((a.cat_wins, a.cat_losses, a.cat_ties), (6, 3, 0))
        self.assertEqual(a.stats["PTS"], 600)
        self.assertAlmostEqual(a.stats["FG%"], 0.50)
        pts = {r.team: r.ranks["PTS"] for r in self.s.season_completed}
        self.assertEqual(pts, {"A": 1, "B": 2, "C": 2, "D": 4})

    def test_completed_season_equals_season_without_a_live_week(self):
        data = LeagueData(teams=["A", "B", "C", "D"], weeks=[self.data.weeks[0]], rosters={})
        s = LeagueStats(data)
        self.assertEqual(s.season, s.season_completed)

    def test_per_week_averages(self):
        a, c = self.season("A"), self.season("C")
        self.assertEqual((a.weeks, c.weeks), (2, 1))           # C had a bye in week 2
        self.assertEqual(a.per_week_stats["PTS"], 500)          # (600 + 400) / 2
        self.assertEqual(c.per_week_stats["PTS"], 550)
        self.assertEqual(a.per_week_stats["FG%"], a.stats["FG%"])
        # Totals favor teams with more weeks; per-week ranks don't.
        self.assertEqual(a.ranks["PTS"], 2)
        self.assertEqual(c.ranks["PTS"], 3)
        self.assertEqual(c.per_week_ranks["PTS"], 2)
        self.assertEqual(a.per_week_ranks["PTS"], 4)
        self.assertAlmostEqual(a.per_week_avg_rank, sum(a.per_week_ranks.values()) / 9)

    def test_season_order_puts_my_team_first(self):
        self.assertEqual([r.team for r in self.s.season], ["C", "A", "B", "D"])

    def test_empty_week_and_team_without_rows(self):
        data = LeagueData(teams=["A", "B", "E"], weeks=[Week(1, False, [])], rosters={})
        s = LeagueStats(data)
        self.assertEqual(s.weekly, [])
        self.assertEqual(s.season[0].stats["FG%"], 0.0)

    def test_sample_league_is_consistent(self):
        s = LeagueStats(SampleLeague.build())
        for wk, rows in s.weeks().items():
            self.assertEqual(min(r.overall_rank for r in rows), 1, wk)
        self.assertEqual(len(s.season), 8)


if __name__ == "__main__":
    unittest.main()
