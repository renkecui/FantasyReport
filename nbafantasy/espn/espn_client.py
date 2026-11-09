from ..common.retry_policy import RetryPolicy
from ..common.sync_error import SyncError
from ..models.categories import Categories
from ..models.league_data import LeagueData
from ..models.matchup_row import MatchupRow
from ..models.player import Player
from ..models.team_roster import TeamRoster
from ..models.week import Week


class EspnClient:
    """Reads one ESPN fantasy basketball league into a LeagueData."""

    POSITIONS = ("PG", "SG", "SF", "PF", "C")
    HEALTHY = (None, "ACTIVE", "NORMAL")
    STATUS_ABBR = {"DAY_TO_DAY": "DTD", "OUT": "O", "INJURY_RESERVE": "IR", "SUSPENSION": "SUSP"}
    FINISHED = ("HOME", "AWAY", "TIE")

    def __init__(self, config, retry=None):
        self.config = config
        self.retry = retry or RetryPolicy()

    # ---------------------------------------------------------------- public
    def fetch(self) -> LeagueData:
        """All weekly matchups plus every team's current roster. Raises SyncError on failure."""
        try:
            return self.retry.run("Getting ESPN data", self._fetch)
        except SyncError:
            raise
        except Exception as e:
            if type(e).__name__ == "ESPNAccessDenied" or "HTTP 401" in str(e):
                raise SyncError(f"ESPN refused the request ({e}). Your ESPN cookies probably expired; "
                                f"update espn_s2 and swid in config.json (README Step 2).")
            raise SyncError(f"Could not get ESPN data ({e}). Google Sheet left unchanged.")

    # ---------------------------------------------------------------- internals
    def _connect(self):
        from espn_api.basketball import League

        kw = {"league_id": self.config.league_id, "year": self.config.season_year}
        if self.config.has_cookies:
            kw.update(espn_s2=self.config.espn_s2, swid=self.config.swid)
        return League(**kw)

    def _fetch(self):
        league = self._connect()
        names = {t.team_id: t.team_name.strip() for t in league.teams}
        current = league.currentMatchupPeriod
        weeks = [self._week(league, names, mp, current) for mp in range(1, current + 1)]
        # Rosters come with the League object, so every team's roster costs no extra request.
        rosters = {names[t.team_id]: self._roster(names[t.team_id], t) for t in league.teams}
        order = [names[t.team_id] for t in sorted(league.teams, key=lambda t: t.team_id)]
        return LeagueData(teams=order, weeks=weeks, rosters=rosters, my_team=self.config.my_team_name)

    def _week(self, league, names, mp, current):
        winners = {}
        for m in league.scoreboard(mp):
            if m.home_team and m.away_team:
                winners[(m.home_team.team_id, m.away_team.team_id)] = m.winner
        week = Week(number=mp, final=mp < current)
        for box in league.box_scores(matchup_period=mp):
            h = getattr(box.home_team, "team_id", box.home_team)
            a = getattr(box.away_team, "team_id", box.away_team)
            if not h or not a:
                continue  # bye
            win = winners.get((h, a), box.winner)
            final = win in self.FINISHED and week.final
            for side, me, opp in (("home", h, a), ("away", a, h)):
                week.rows.append(self._matchup_row(box, side, names[me], names[opp], win, final))
        return week

    def _matchup_row(self, box, side, team, opponent, win, final):
        stats = getattr(box, f"{side}_stats") or {}
        if not final:
            result = "Live"
        elif win == "TIE":
            result = "T"
        else:
            result = "W" if win.lower() == side else "L"
        return MatchupRow(
            team=team, opponent=opponent,
            cat_wins=getattr(box, f"{side}_wins"), cat_losses=getattr(box, f"{side}_losses"),
            cat_ties=getattr(box, f"{side}_ties"), result=result,
            stats={c: (stats.get(c) or {}).get("value", 0) for c in Categories.ALL})

    def _roster(self, team_name, team):
        return TeamRoster(team=team_name, players=[self._player(p) for p in team.roster])

    def _player(self, p):
        key = f"{self.config.season_year}_total"
        avg = ((p.stats or {}).get(key) or {}).get("avg") or {}
        status = "" if p.injuryStatus in self.HEALTHY else self.STATUS_ABBR.get(p.injuryStatus, p.injuryStatus)
        return Player(
            slot=p.lineupSlot, name=p.name, nba_team=p.proTeam,
            positions=", ".join(s for s in p.eligibleSlots if s in self.POSITIONS),
            status=status,
            stats={k: avg.get(k, 0) for k in Categories.PLAYER_STATS})
