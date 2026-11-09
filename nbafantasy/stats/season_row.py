from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SeasonRow:
    """One team's season: matchup record, category record, totals and league ranks."""
    team: str
    wins: int
    losses: int
    ties: int
    cat_wins: int
    cat_losses: int
    cat_ties: int
    stats: Dict[str, float]  # FG%/FT%: average of weekly %; others: sum of weeks
    ranks: Dict[str, int]    # per category, 1 = best in the league

    @property
    def record(self):
        return f"{self.wins}-{self.losses}-{self.ties}"

    @property
    def avg_rank(self):
        return sum(self.ranks.values()) / len(self.ranks) if self.ranks else 0.0
