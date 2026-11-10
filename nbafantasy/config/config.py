import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """The contents of config.json."""
    league_id: int
    season_year: int
    my_team_name: str = ""
    sheet_title: str = "The Boys Fantasy Report"
    espn_s2: str = ""
    swid: str = ""
    publish_site: bool = False

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
            publish_site=raw.get("publish_site") is True,
        )

    @property
    def has_cookies(self):
        return bool(self.espn_s2 and self.swid)
