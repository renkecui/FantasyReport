from dataclasses import dataclass
from typing import Dict

from ..models.matchup_row import MatchupRow


@dataclass(frozen=True)
class WeeklyRow:
    """One team's matchup in one week, with its ranks among every team that week."""
    week: int
    final: bool
    row: MatchupRow
    ranks: Dict[str, int]   # per category, 1 = best that week
    avg_rank: float         # average of the 9 category ranks
    overall_rank: int       # rank of avg_rank that week (lower average = better)
