import os
import shutil

from .league_json import LeagueJson
from ..common.files import Files


class SiteBuilder:
    """Writes the site folder: a fresh copy of web/ (including its subfolders) plus league.json."""

    DATA_FILE = "league.json"

    def __init__(self, web_dir, out_dir):
        self.web_dir = web_dir
        self.out_dir = out_dir

    def build(self, league: LeagueJson):
        """Returns the folder it wrote. Files no longer in web/ are removed from it."""
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir)
        shutil.copytree(self.web_dir, self.out_dir, ignore=shutil.ignore_patterns(".*"))
        Files.write(os.path.join(self.out_dir, self.DATA_FILE), league.to_text())
        return self.out_dir
