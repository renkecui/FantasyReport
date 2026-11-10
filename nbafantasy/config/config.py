import json
import os
from dataclasses import dataclass
from typing import Mapping, Optional

from ..common.sync_error import SyncError


@dataclass(frozen=True)
class Config:
    """The league settings: config.json on the Mac, or environment variables (GitHub Actions)."""
    league_id: int
    season_year: int
    my_team_name: str = ""
    sheet_title: str = "The Boys Fantasy Report"
    espn_s2: str = ""
    swid: str = ""
    publish_site: bool = False

    # config.json key -> environment variable used when there is no config.json
    ENV = {
        "league_id": "LEAGUE_ID",
        "season_year": "SEASON_YEAR",
        "my_team_name": "MY_TEAM_NAME",
        "sheet_title": "SHEET_TITLE",
        "espn_s2": "ESPN_S2",
        "swid": "ESPN_SWID",
        "publish_site": "PUBLISH_SITE",
    }

    @classmethod
    def load(cls, path, env: Optional[Mapping[str, str]] = None):
        """config.json if it exists, else the environment variables in ENV."""
        if os.path.exists(path):
            with open(path) as f:
                return cls.from_dict(json.load(f))
        return cls.from_env(os.environ if env is None else env)

    @classmethod
    def from_env(cls, env: Mapping[str, str]):
        missing = [cls.ENV[k] for k in ("league_id", "season_year") if not env.get(cls.ENV[k])]
        if missing:
            raise SyncError(f"config.json not found and {', '.join(missing)} not set. "
                            f"Copy config.example.json to config.json (or set the environment variables).")
        raw = {key: env.get(var, "") for key, var in cls.ENV.items()}
        raw["publish_site"] = raw["publish_site"].strip().lower() in ("1", "true", "yes")
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw):
        return cls(
            league_id=int(raw["league_id"]),
            season_year=int(raw["season_year"]),
            my_team_name=(raw.get("my_team_name") or "").strip(),
            sheet_title=raw.get("sheet_title") or cls.sheet_title,
            espn_s2=(raw.get("espn_s2") or "").strip(),
            swid=(raw.get("swid") or "").strip(),
            publish_site=raw.get("publish_site") is True,
        )

    @property
    def has_cookies(self):
        return bool(self.espn_s2 and self.swid)
