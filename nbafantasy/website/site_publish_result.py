from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SitePublishResult:
    changed: bool
    url: Optional[str]
