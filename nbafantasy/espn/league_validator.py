from ..common.sync_error import SyncError
from ..models.categories import Categories


class LeagueValidator:
    """Makes sure the ESPN data looks complete before it replaces anything."""

    MAX_REPORTED = 5

    def __init__(self, config):
        self.config = config

    def validate(self, data):
        problems = self.problems(data)
        if problems:
            raise SyncError("ESPN data looks wrong, Google Sheet left unchanged: "
                            + "; ".join(problems[:self.MAX_REPORTED]))

    def problems(self, data):
        return self._teams(data) + self._weeks(data) + self._rosters(data) + self._my_team(data)

    def _teams(self, data):
        n = len(data.teams)
        return [f"only {n} teams came back from ESPN"] if n < 2 else []

    def _weeks(self, data):
        if not data.weeks:
            raise SyncError("No matchups found. Check league_id and season_year in config.json.")
        problems = []
        n = len(data.teams)
        # Each matchup gives 2 rows. With an odd number of teams one team has a bye each week.
        expected = n - n % 2
        for wk in data.weeks:
            if wk.final and len(wk.rows) != expected:
                problems.append(f"week {wk.number} has {len(wk.rows)} rows, expected {expected} for {n} teams")
            for row in wk.rows:
                missing = [c for c in Categories.ALL if row.stats.get(c) is None]
                if missing:
                    problems.append(f"week {wk.number} {row.team} is missing {', '.join(missing)}")
                if wk.final and row.cat_wins + row.cat_losses + row.cat_ties != len(Categories.ALL):
                    problems.append(f"week {wk.number} {row.team} category score doesn't add up to {len(Categories.ALL)}")
        return problems

    def _rosters(self, data):
        empty = [t for t in data.teams if not (data.rosters.get(t) and data.rosters[t].players)]
        return [f"no roster for {', '.join(empty)}"] if empty else []

    def _my_team(self, data):
        my = self.config.my_team_name
        if my and my not in data.teams:
            return [f"team '{my}' not found (ESPN names: {', '.join(data.teams)}); "
                    f"check my_team_name in config.json"]
        return []
