from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SitePublishResult:
    """The outcome of publishing the website: whether anything changed, and the site's address."""
    changed: bool
    url: Optional[str]
