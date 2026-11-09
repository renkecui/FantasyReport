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
        # The same totals from finished weeks only, leaving out the week in progress.
        self.season_completed: List[SeasonRow] = self._season(final_only=True)

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
    def _season(self, final_only=False):
        """Season Totals tab: W/L/T = COUNTIFS(result), so Live weeks don't count toward the
        record; Cat W/L/T and counting stats = SUMIFS over every week (including the live one);
        FG%/FT% = AVERAGEIFS of the weekly %; league rank = RANK (TO ascending).
        With final_only, the week in progress is left out of everything."""
        teams = self.data.teams_mine_first()
        by_team: Dict[str, List[MatchupRow]] = {t: [] for t in teams}
        for w in self.weekly:
            if final_only and not w.final:
                continue
            by_team.setdefault(w.row.team, []).append(w.row)

        partial = []
        for team in teams:
            rows = by_team[team]
            results = [r.result for r in rows]
            stats, per_week = {}, {}
            for c in Categories.ALL:
                vals = [r.stats[c] for r in rows]
                mean = sum(vals) / len(vals) if vals else 0.0
                stats[c] = mean if Categories.is_percent(c) else sum(vals)
                per_week[c] = mean
            partial.append((team, results, rows, stats, per_week))

        per_cat = self._league_ranks([p[3] for p in partial])
        per_week_ranks = self._league_ranks([p[4] for p in partial])
        out = []
        for i, (team, results, rows, stats, per_week) in enumerate(partial):
            out.append(SeasonRow(
                team=team,
                wins=results.count("W"), losses=results.count("L"), ties=results.count("T"),
                cat_wins=sum(r.cat_wins for r in rows),
                cat_losses=sum(r.cat_losses for r in rows),
                cat_ties=sum(r.cat_ties for r in rows),
                stats=stats,
                ranks={c: per_cat[c][i] for c in Categories.ALL},
                weeks=len(rows),
                per_week_stats=per_week,
                per_week_ranks={c: per_week_ranks[c][i] for c in Categories.ALL}))
        return out

    @staticmethod
    def _league_ranks(team_stats: List[Dict[str, float]]) -> Dict[str, List[int]]:
        """For each category, every team's league rank (in the order given)."""
        return {c: Ranking.competition([s[c] for s in team_stats], Categories.lower_is_better(c))
                for c in Categories.ALL}
