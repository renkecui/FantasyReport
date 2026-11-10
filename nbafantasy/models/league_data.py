from dataclasses import dataclass
from typing import Dict, List

from .team_roster import TeamRoster
from .week import Week


@dataclass
class LeagueData:
    """Everything read from ESPN for one run: teams, weeks of matchups and rosters."""
    teams: List[str]                      # in ESPN team-id order
    weeks: List[Week]
    rosters: Dict[str, TeamRoster]        # every team's current roster, by team name
    my_team: str = ""

    def teams_mine_first(self):
        """Team names with my_team (config.json my_team_name) first, for the Google Sheet."""
        if self.my_team in self.teams:
            return [self.my_team] + [t for t in self.teams if t != self.my_team]
        return list(self.teams)

    @property
    def live_weeks(self):
        """Numbers of the weeks still in progress."""
        return [w.number for w in self.weeks if not w.final]

    def matchup_rows(self):
        """(week, row) for every row, in week order."""
        return [(wk, row) for wk in self.weeks for row in wk.rows]
