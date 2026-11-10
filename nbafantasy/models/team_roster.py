from dataclasses import dataclass, field
from typing import List

from .player import Player


@dataclass
class TeamRoster:
    """A fantasy team's current players."""
    team: str
    players: List[Player] = field(default_factory=list)

    def in_lineup_order(self):
        """Starters by position, then bench, then IR (stable within a slot)."""
        return sorted(self.players, key=lambda p: p.slot_rank)
