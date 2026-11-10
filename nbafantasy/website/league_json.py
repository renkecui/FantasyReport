import json
from datetime import datetime, timezone

from ..models.categories import Categories
from ..models.league_data import LeagueData
from ..stats.league_stats import LeagueStats
from ..stats.season_row import SeasonRow
from ..stats.weekly_row import WeeklyRow


class LeagueJson:
    """The contents of league.json, built from an explicit allow-list of fields."""

    # 2: no "my_team" (the website gets it from whoever is logged in), no team colors (themes
    #    are on the website), teams in ESPN order.
    SCHEMA_VERSION = 2

    def __init__(self, data: LeagueData, title: str, season_year: int, now=None):
        self.data = data
        self.stats = LeagueStats(data)
        self.title = title
        self.season_year = season_year
        self.now = now or datetime.now(timezone.utc)

    def payload(self):
        data = self.data
        teams = list(data.teams)  # ESPN order: no team is singled out on the public site
        weeks = self.stats.weeks()
        return {
            "schema_version": self.SCHEMA_VERSION,
            "generated_at": self.now.astimezone(timezone.utc).isoformat(timespec="seconds"),
            "title": self.title,
            "season_year": self.season_year,
            "categories": list(Categories.ALL),
            "lower_is_better": sorted(Categories.LOWER_IS_BETTER),
            "player_stats": list(Categories.PLAYER_STATS),
            "teams": [{"name": t} for t in teams],  # colors come from the website's themes
            "season": self._in_order(self.stats.season, teams),
            "season_completed": self._in_order(self.stats.season_completed, teams),
            "weeks": [{"number": wk.number, "final": wk.final,
                       "rows": [self._weekly_row(w) for w in weeks.get(wk.number, [])]}
                      for wk in data.weeks],
            "rosters": {t: self._roster(t) for t in teams},
        }

    def to_text(self):
        return json.dumps(self.payload(), ensure_ascii=False, separators=(",", ":"))

    # ---------------------------------------------------------------- rows
    @staticmethod
    def compact(v, digits=4):
        """Round floats so the JSON stays small; keep whole numbers as ints."""
        if isinstance(v, float):
            return int(v) if v.is_integer() else round(v, digits)
        return v

    @classmethod
    def _season_row(cls, r: SeasonRow):
        return {"team": r.team, "wins": r.wins, "losses": r.losses, "ties": r.ties,
                "record": r.record, "cat_wins": r.cat_wins, "cat_losses": r.cat_losses,
                "cat_ties": r.cat_ties, "avg_rank": cls.compact(r.avg_rank, 2),
                "stats": {c: cls.compact(v) for c, v in r.stats.items()}, "ranks": r.ranks,
                "weeks": r.weeks,
                "per_week": {"stats": {c: cls.compact(v, 2 if not Categories.is_percent(c) else 4)
                                       for c, v in r.per_week_stats.items()},
                             "ranks": r.per_week_ranks, "avg_rank": cls.compact(r.per_week_avg_rank, 2)}}

    @classmethod
    def _weekly_row(cls, w: WeeklyRow):
        r = w.row
        return {"team": r.team, "opponent": r.opponent, "cat_wins": r.cat_wins,
                "cat_losses": r.cat_losses, "cat_ties": r.cat_ties, "result": r.result,
                "tiebreak": r.decided_by_tiebreak, "avg_rank": cls.compact(w.avg_rank, 2),
                "overall_rank": w.overall_rank,
                "stats": {c: cls.compact(r.stats[c]) for c in Categories.ALL}, "ranks": w.ranks}

    @classmethod
    def _in_order(cls, rows, teams):
        by_team = {r.team: r for r in rows}
        return [cls._season_row(by_team[t]) for t in teams if t in by_team]

    def _roster(self, team):
        roster = self.data.rosters.get(team)
        players = roster.in_lineup_order() if roster else []
        out = []
        for p in players:
            s = {k: self.compact(p.stats.get(k, 0), 2) for k in Categories.PLAYER_STATS}
            fga, fta = p.stats.get("FGA", 0), p.stats.get("FTA", 0)
            s["FG%"] = self.compact(p.stats.get("FGM", 0) / fga if fga else 0.0)  # made ÷ attempted, like the sheet
            s["FT%"] = self.compact(p.stats.get("FTM", 0) / fta if fta else 0.0)
            out.append({"slot": p.slot_label, "name": p.name, "nba_team": p.nba_team,
                        "positions": p.positions, "status": p.status, "stats": s})
        return out
