from dataclasses import dataclass
from typing import List

from ..config.config import Config


@dataclass(frozen=True)
class RunOptions:
    """The command-line flags for one run.

      --login      sign in to Google again first
      --excel      local files only: save the .xlsx and build the site in data/site, publish nothing
      --site-only  skip the .xlsx and Google; build the site and publish it to GitHub Pages
      --no-site    don't publish the site (it is still built in data/site)
    """
    login: bool = False
    local_only: bool = False
    site_only: bool = False
    no_site: bool = False

    @classmethod
    def from_args(cls, args: List[str]):
        a = set(args)
        return cls(login="--login" in a, local_only="--excel" in a,
                   site_only="--site-only" in a, no_site="--no-site" in a)

    @property
    def build_workbook(self):
        return not self.site_only

    @property
    def publish_sheet(self):
        return not (self.local_only or self.site_only)

    def publish_site(self, config: Config):
        """Published when config.json has "publish_site": true, or with --site-only."""
        if self.local_only or self.no_site:
            return False
        return config.publish_site or self.site_only
