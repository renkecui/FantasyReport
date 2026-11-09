import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Paths:
    """Every file the app reads or writes.

    Files you provide stay in the project folder (config.json, credentials.json).
    Everything the app writes goes in data/ (git-ignored).
    """
    root: str

    # Files that older versions wrote to the project folder; migrate_legacy() moves them to data/.
    LEGACY = ("token.json", "sheet_id.txt", "sync_state.json", "The_Boys_League_Stats.xlsx", "backups")

    @property
    def data_dir(self):
        return os.path.join(self.root, "data")

    def _data(self, name):
        return os.path.join(self.data_dir, name)

    # ---- you provide these
    @property
    def config(self):
        return os.path.join(self.root, "config.json")

    @property
    def credentials(self):
        return os.path.join(self.root, "credentials.json")

    # ---- the app writes these
    @property
    def token(self):
        return self._data("token.json")

    @property
    def sheet_id(self):
        return self._data("sheet_id.txt")

    @property
    def state(self):
        return self._data("sync_state.json")

    @property
    def backups(self):
        return self._data("backups")

    @property
    def lock(self):
        return self._data(".update.lock")

    @property
    def local_xlsx(self):
        return self._data("The_Boys_League_Stats.xlsx")

    def prepare(self):
        """Create data/ and move files left in the project folder by older versions.
        Returns the names moved. Never overwrites a file already in data/."""
        os.makedirs(self.data_dir, exist_ok=True)
        moved = []
        for name in self.LEGACY:
            old, new = os.path.join(self.root, name), self._data(name)
            if os.path.exists(old) and not os.path.exists(new):
                os.replace(old, new)
                moved.append(name)
        return moved


@dataclass(frozen=True)
class Config:
    """The contents of config.json."""
    league_id: int
    season_year: int
    my_team_name: str = ""
    sheet_title: str = "The Boys League Stats"
    espn_s2: str = ""
    swid: str = ""

    @classmethod
    def load(cls, path):
        with open(path) as f:
            raw = json.load(f)
        return cls(
            league_id=int(raw["league_id"]),
            season_year=int(raw["season_year"]),
            my_team_name=(raw.get("my_team_name") or "").strip(),
            sheet_title=raw.get("sheet_title") or cls.sheet_title,
            espn_s2=raw.get("espn_s2") or "",
            swid=raw.get("swid") or "",
        )

    @property
    def has_cookies(self):
        return bool(self.espn_s2 and self.swid)
