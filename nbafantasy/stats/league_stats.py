from typing import Dict, List

from .ranking import Ranking
from .season_row import SeasonRow
from .weekly_row import WeeklyRow
from ..models.categories import Categories
from ..models.league_data import LeagueData
from ..models.matchup_row import MatchupRow


class LeagueStats:
    """Weekly ranks and season totals for a LeagueData, matching the workbook's formulas."""

    def __init__(self, data: LeagueData):
        self.data = data
        self.weekly: List[WeeklyRow] = []
        for wk in data.weeks:
            self.weekly.extend(self._rank_week(wk.number, wk.final, wk.rows))
        self.season: List[SeasonRow] = self._season()

    def weeks(self) -> Dict[int, List[WeeklyRow]]:
        """Weekly rows grouped by week number, in matchup order."""
        out: Dict[int, List[WeeklyRow]] = {}
        for w in self.weekly:
            out.setdefault(w.week, []).append(w)
        return out

    # ---------------------------------------------------------------- weekly
    @staticmethod
    def _rank_week(number, final, rows):
        """Weekly Stats tab: rank = COUNTIFS(same week, stat better)+1;
        Avg Rank = AVERAGE(category ranks); Overall = COUNTIFS(same week, avg lower)+1."""
        if not rows:
            return []
        per_cat = {c: Ranking.competition([r.stats[c] for r in rows], Categories.lower_is_better(c))
                   for c in Categories.ALL}
        ranks = [{c: per_cat[c][i] for c in Categories.ALL} for i in range(len(rows))]
        avgs = [sum(rk.values()) / len(Categories.ALL) for rk in ranks]
        overall = Ranking.competition(avgs, lower_is_better=True)
        return [WeeklyRow(number, final, row, ranks[i], avgs[i], overall[i]) for i, row in enumerate(rows)]

    # ---------------------------------------------------------------- season
    def _season(self):
        """Season Totals tab: W/L/T = COUNTIFS(result), so Live weeks don't count toward the
        record; Cat W/L/T and counting stats = SUMIFS over every week (including the live one);
        FG%/FT% = AVERAGEIFS of the weekly %; league rank = RANK (TO ascending)."""
        teams = self.data.teams_mine_first()
        by_team: Dict[str, List[MatchupRow]] = {t: [] for t in teams}
        for w in self.weekly:
            by_team.setdefault(w.row.team, []).append(w.row)

        partial = []
        for team in teams:
            rows = by_team[team]
            results = [r.result for r in rows]
            stats = {}
            for c in Categories.ALL:
                vals = [r.stats[c] for r in rows]
                if Categories.is_percent(c):
                    stats[c] = sum(vals) / len(vals) if vals else 0.0
                else:
                    stats[c] = sum(vals)
            partial.append((team, results, rows, stats))

        per_cat = {c: Ranking.competition([p[3][c] for p in partial], Categories.lower_is_better(c))
                   for c in Categories.ALL}
        out = []
        for i, (team, results, rows, stats) in enumerate(partial):
            out.append(SeasonRow(
                team=team,
                wins=results.count("W"), losses=results.count("L"), ties=results.count("T"),
                cat_wins=sum(r.cat_wins for r in rows),
                cat_losses=sum(r.cat_losses for r in rows),
                cat_ties=sum(r.cat_ties for r in rows),
                stats=stats,
                ranks={c: per_cat[c][i] for c in Categories.ALL}))
        return out
