from dataclasses import dataclass
from typing import Dict, List, Optional

from .team_roster import TeamRoster
from .week import Week


@dataclass
class LeagueData:
    teams: List[str]                      # in ESPN team-id order
    weeks: List[Week]
    rosters: Dict[str, TeamRoster]        # every team's current roster, by team name
    my_team: str = ""

    def teams_mine_first(self):
        if self.my_team in self.teams:
            return [self.my_team] + [t for t in self.teams if t != self.my_team]
        return list(self.teams)

    @property
    def my_roster(self) -> Optional[TeamRoster]:
        return self.rosters.get(self.my_team)

    @property
    def live_weeks(self):
        return [w.number for w in self.weeks if not w.final]

    def matchup_rows(self):
        """(week, row) for every row, in week order."""
        return [(wk, row) for wk in self.weeks for row in wk.rows]
