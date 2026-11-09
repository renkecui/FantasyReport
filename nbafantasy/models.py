"""Plain data objects passed from the ESPN client to the validator and the workbook."""
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional

# The 9 head-to-head categories, in sheet order.
CATS = ("FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS")
# Per-game averages shown for each player.
PLAYER_STATS = ("MIN", "FGM", "FGA", "FTM", "FTA", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS")


@dataclass(frozen=True)
class MatchupRow:
    """One team's side of one weekly matchup."""
    team: str
    opponent: str
    cat_wins: int
    cat_losses: int
    cat_ties: int
    result: str  # "W", "L", "T" or "Live"
    stats: Dict[str, float]

    @property
    def decided_by_tiebreak(self):
        return self.result in ("W", "L") and self.cat_wins == self.cat_losses


@dataclass
class Week:
    number: int
    final: bool
    rows: List[MatchupRow] = field(default_factory=list)


@dataclass(frozen=True)
class Player:
    slot: str        # ESPN lineup slot, e.g. "PG", "UT", "BE", "IR"
    name: str
    nba_team: str
    positions: str   # e.g. "PG, SG"
    status: str      # "" when healthy, else "DTD", "O", "IR", "SUSP", ...
    stats: Dict[str, float]  # season per-game averages, keys from PLAYER_STATS

    # ESPN slot names (espn_api POSITION_MAP). Starters first, then UTIL, bench, IR.
    SLOT_ORDER: ClassVar[Dict[str, int]] = {
        "PG": 0, "SG": 1, "SG/SF": 2, "G/F": 3, "G": 4, "SF": 5, "PF": 6, "F": 7,
        "PF/C": 8, "F/C": 9, "C": 10, "UT": 11, "BE": 12, "IR": 13}
    SLOT_LABELS: ClassVar[Dict[str, str]] = {"BE": "Bench", "UT": "UTIL"}

    @property
    def slot_label(self):
        return self.SLOT_LABELS.get(self.slot, self.slot)

    @property
    def slot_rank(self):
        return self.SLOT_ORDER.get(self.slot, self.SLOT_ORDER["UT"])


@dataclass
class TeamRoster:
    team: str
    players: List[Player] = field(default_factory=list)

    def in_lineup_order(self):
        """Starters by position, then bench, then IR (stable within a slot)."""
        return sorted(self.players, key=lambda p: p.slot_rank)


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
