from dataclasses import dataclass, field
from typing import List

from .matchup_row import MatchupRow


@dataclass
class Week:
    """One scoring week: its number, whether it is finished, and every team's matchup row."""
    number: int
    final: bool
    rows: List[MatchupRow] = field(default_factory=list)
