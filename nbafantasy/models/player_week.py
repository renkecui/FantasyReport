from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class PlayerWeek:
    """One player's NBA games in one fantasy week: how many, and their summed stats."""
    games: int
    totals: Dict[str, float] = field(default_factory=dict)  # keys from Categories.PLAYER_STATS
