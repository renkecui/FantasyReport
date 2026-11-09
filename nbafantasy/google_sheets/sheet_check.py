from dataclasses import dataclass, field
from typing import List


@dataclass
class SheetCheck:
    ok_to_update: bool  # False means: make a new sheet instead
    edited: bool = False
    warnings: List[str] = field(default_factory=list)
