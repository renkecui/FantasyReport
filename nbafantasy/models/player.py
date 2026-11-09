from dataclasses import dataclass
from typing import ClassVar, Dict


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
