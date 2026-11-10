import json
import urllib.request
from typing import Dict

from ..common.logger import Logger
from ..common.retry_policy import RetryPolicy
from ..common.sync_error import SyncError
from ..models.categories import Categories
from ..models.league_data import LeagueData
from ..models.matchup_row import MatchupRow
from ..models.player import Player
from ..models.player_week import PlayerWeek
from ..models.team_roster import TeamRoster
from ..models.week import Week


class EspnClient:
    """Reads one ESPN fantasy basketball league into a LeagueData."""

    POSITIONS = ("PG", "SG", "SF", "PF", "C")
    HEALTHY = (None, "ACTIVE", "NORMAL")
    STATUS_ABBR = {"DAY_TO_DAY": "DTD", "OUT": "O", "INJURY_RESERVE": "IR", "SUSPENSION": "SUSP"}
    FINISHED = ("HOME", "AWAY", "TIE")
    # Public: ESPN's fantasy basketball game, including the season it currently runs (currentSeasonId).
    GAME_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba"

    def __init__(self, config, retry=None, current_season=None):
        self.config = config
        self.retry = retry or RetryPolicy()
        self._current_season = current_season or self._espn_current_season
        self.year = 0  # the season being read, set by fetch()

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
                                f"get fresh ones (docs/SETUP.md step 3) and update the ESPN_S2 / SWID secrets (or config.json).")
            raise SyncError(f"Could not get ESPN data ({e}). Google Sheet left unchanged.")

    # ---------------------------------------------------------------- internals
    def season_year(self) -> int:
        """season_year from the settings, or else the season ESPN says is current (2027 = 2026-27)."""
        if self.config.season_year:
            return self.config.season_year
        year = self._current_season()
        if not isinstance(year, int) or year < 2000:
            raise SyncError(f"ESPN didn't say which season is current (got {year!r}). Set season_year.")
        return year

    @classmethod
    def _espn_current_season(cls):
        req = urllib.request.Request(cls.GAME_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.load(res).get("currentSeasonId")

    def _connect(self):
        from espn_api.basketball import League

        kw = {"league_id": self.config.league_id, "year": self.year}
        if self.config.has_cookies:
            kw.update(espn_s2=self.config.espn_s2, swid=self.config.swid)
        return League(**kw)

    def _fetch(self):
        self.year = self.season_year()
        league = self._connect()
        names = {t.team_id: t.team_name.strip() for t in league.teams}
        current = league.currentMatchupPeriod
        weeks = [self._week(league, names, mp, current) for mp in range(1, current + 1)]
        # Rosters come with the League object, so every team's roster costs no extra request.
        # Each player's games this season take one more request for all of them.
        player_weeks = self._player_weeks(league, current)
        rosters = {names[t.team_id]: self._roster(names[t.team_id], t, player_weeks) for t in league.teams}
        order = [names[t.team_id] for t in sorted(league.teams, key=lambda t: t.team_id)]
        return LeagueData(teams=order, weeks=weeks, rosters=rosters, my_team=self.config.my_team_name,
                          season_year=self.year, draft_order=self.draft_order(league, names))

    @staticmethod
    def draft_order(league, names):
        """Team names in first-round pick order, or [] if the league hasn't drafted."""
        first = sorted((p for p in getattr(league, "draft", None) or []
                        if p.round_num == 1 and p.team is not None and p.round_pick is not None),
                       key=lambda p: p.round_pick)
        order = [names.get(p.team.team_id) for p in first]
        return [t for t in order if t] if len(set(order)) == len(order) else []

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

    def _player_weeks(self, league, current):
        """{playerId: {week: PlayerWeek}} for every rostered player, from ESPN's player cards.
        Empty if ESPN won't give them: the website then shows season stats only."""
        ids = [p.playerId for t in league.teams for p in t.roster]
        if not ids:
            return {}
        try:
            cards = league.player_info(playerId=ids)
        except Exception as e:  # a nice-to-have: never fail the whole update for it
            Logger().warning(f"Couldn't get players' game-by-game stats from ESPN ({e}); "
                             "the website shows season stats only.")
            return {}
        cards = cards if isinstance(cards, list) else [cards] if cards else []
        periods = {mp: league.matchup_ids.get(mp, []) for mp in range(1, current + 1)}
        return {c.playerId: self.group_games(c.stats or {}, periods) for c in cards}

    @staticmethod
    def group_games(stats, periods) -> Dict[int, PlayerWeek]:
        """Sum a player's games into fantasy weeks.

        stats: espn_api Player.stats, where a game's entry is keyed by its scoring period (day),
        e.g. "12": {"total": {"PTS": 31, ...}}. periods: {week: [scoring period ids]}.
        Weeks without a game played are left out."""
        weeks = {}
        for week, days in periods.items():
            games, totals = 0, {k: 0.0 for k in Categories.PLAYER_STATS}
            for day in days:
                game = (stats.get(str(day)) or {}).get("total") or {}
                if not (game.get("GP") or game.get("MIN")):
                    continue  # no game that day, or did not play
                games += 1
                for k in Categories.PLAYER_STATS:
                    totals[k] += game.get(k) or 0
            if games:
                weeks[week] = PlayerWeek(games=games, totals=totals)
        return weeks

    def _roster(self, team_name, team, player_weeks=None):
        weeks = player_weeks or {}
        return TeamRoster(team=team_name, players=[self._player(p, weeks.get(getattr(p, "playerId", None)))
                                                   for p in team.roster])

    def _player(self, p, weeks=None):
        key = f"{self.year}_total"
        avg = ((p.stats or {}).get(key) or {}).get("avg") or {}
        status = "" if p.injuryStatus in self.HEALTHY else self.STATUS_ABBR.get(p.injuryStatus, p.injuryStatus)
        return Player(
            slot=p.lineupSlot, name=p.name, nba_team=p.proTeam,
            positions=", ".join(s for s in p.eligibleSlots if s in self.POSITIONS),
            status=status,
            stats={k: avg.get(k, 0) for k in Categories.PLAYER_STATS},
            weeks=weeks or {})
