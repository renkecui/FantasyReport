from dataclasses import dataclass
from typing import Dict


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
