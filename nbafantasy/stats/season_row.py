from dataclasses import dataclass, field
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
    weeks: int = 0           # weeks counted (a bye week doesn't count)
    # The same categories averaged per week (FG%/FT% are already averages), and their league ranks.
    per_week_stats: Dict[str, float] = field(default_factory=dict)
    per_week_ranks: Dict[str, int] = field(default_factory=dict)

    @property
    def record(self):
        return f"{self.wins}-{self.losses}-{self.ties}"

    @property
    def avg_rank(self):
        return self._mean(self.ranks)

    @property
    def per_week_avg_rank(self):
        return self._mean(self.per_week_ranks)

    @staticmethod
    def _mean(ranks: Dict[str, int]):
        return sum(ranks.values()) / len(ranks) if ranks else 0.0
