"""A made-up league for tests and for previewing the website without ESPN."""
import random

from nbafantasy.models import Categories, LeagueData, MatchupRow, Player, PlayerWeek, TeamRoster, Week


class SampleLeague:
    """A made-up 8-team league: SampleLeague.build() -> LeagueData."""

    TEAMS = ["Splash Bros", "Glass Cleaners", "Dime Dropper$", "Block Party", "Free Throw Fails",
             "Pick & Roll Call", "Bench Mob", "<Tank> Commanders"]
    SLOTS = ["PG", "SG", "SF", "PF", "C", "G", "F", "UT", "UT", "UT", "BE", "BE", "IR"]
    FIRST = ["Jalen", "Marcus", "Tyrese", "Devin", "Jaylen", "Luka", "Anthony", "Bam", "Scottie",
             "Darius", "Myles", "Franz", "Alperen", "Cade", "Evan", "Desmond"]
    LAST = ["Brooks", "Carter", "Daniels", "Ellis", "Foster", "Grant", "Hayes", "Irving", "Jones",
            "King", "Lewis", "Moore", "Nash", "Owens", "Price", "Reed"]
    NBA = ["BOS", "DEN", "OKC", "NYK", "MIL", "PHX", "SAC", "MIN", "LAL", "DAL", "IND", "ORL"]

    @staticmethod
    def _week_stats(rng):
        return {"FG%": round(rng.uniform(0.43, 0.51), 4), "FT%": round(rng.uniform(0.72, 0.85), 4),
                "3PM": rng.randint(35, 75), "REB": rng.randint(150, 260), "AST": rng.randint(90, 170),
                "STL": rng.randint(20, 45), "BLK": rng.randint(10, 35), "TO": rng.randint(45, 85),
                "PTS": rng.randint(450, 700)}

    @staticmethod
    def _score(a, b):
        w = l = t = 0
        for c in Categories.ALL:
            if a[c] == b[c]:
                t += 1
            elif (a[c] < b[c]) if c == "TO" else (a[c] > b[c]):
                w += 1
            else:
                l += 1
        return w, l, t

    @staticmethod
    def _player(rng, slot, n_weeks=0):
        fgm, ftm = rng.uniform(2, 10), rng.uniform(0.5, 7)
        stats = {"MIN": rng.uniform(14, 37), "FGM": fgm, "FGA": fgm / rng.uniform(0.42, 0.6),
                 "FTM": ftm, "FTA": ftm / rng.uniform(0.65, 0.92), "3PM": rng.uniform(0, 4),
                 "REB": rng.uniform(2, 12), "AST": rng.uniform(1, 9), "STL": rng.uniform(0.3, 1.8),
                 "BLK": rng.uniform(0.1, 2.2), "TO": rng.uniform(0.6, 3.8), "PTS": rng.uniform(6, 32)}
        return Player(slot=slot, name=f"{rng.choice(SampleLeague.FIRST)} {rng.choice(SampleLeague.LAST)}",
                      nba_team=rng.choice(SampleLeague.NBA),
                      positions=", ".join(sorted(rng.sample(["PG", "SG", "SF", "PF", "C"], rng.randint(1, 2)))),
                      status=rng.choice(["", "", "", "", "", "DTD", "O"]) if slot != "IR" else "IR",
                      stats={k: round(stats[k], 1) for k in Categories.PLAYER_STATS},
                      weeks=SampleLeague._player_weeks(rng, stats, n_weeks))

    @staticmethod
    def _player_weeks(rng, per_game, n_weeks):
        """0-4 games a week around the season averages; weeks without games left out."""
        weeks = {}
        for n in range(1, n_weeks + 1):
            games = rng.randint(0, 4)
            if games:
                weeks[n] = PlayerWeek(games, {k: round(per_game[k] * games * rng.uniform(0.7, 1.3), 1)
                                              for k in Categories.PLAYER_STATS})
        return weeks

    @classmethod
    def build(cls, n_weeks=5, seed=26) -> LeagueData:
        """8 teams, `n_weeks` weeks (the last one Live), full rosters."""
        rng = random.Random(seed)
        weeks = []
        for n in range(1, n_weeks + 1):
            final = n < n_weeks
            order = cls.TEAMS[:]
            rng.shuffle(order)
            wk = Week(number=n, final=final)
            for a, b in zip(order[::2], order[1::2]):
                sa, sb = cls._week_stats(rng), cls._week_stats(rng)
                wa, la, ta = cls._score(sa, sb)
                if not final:
                    ra = rb = "Live"
                elif wa == la:
                    ra, rb = ("W", "L") if rng.random() < 0.5 else ("L", "W")  # league tiebreaker
                else:
                    ra, rb = ("W", "L") if wa > la else ("L", "W")
                wk.rows.append(MatchupRow(a, b, wa, la, ta, ra, sa))
                wk.rows.append(MatchupRow(b, a, la, wa, ta, rb, sb))
            weeks.append(wk)
        rosters = {t: TeamRoster(t, [cls._player(rng, s, n_weeks) for s in cls.SLOTS]) for t in cls.TEAMS}
        return LeagueData(teams=list(cls.TEAMS), weeks=weeks, rosters=rosters, my_team=cls.TEAMS[2])
