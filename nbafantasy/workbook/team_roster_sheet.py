from openpyxl.styles import Border

from .sheet_writer import SheetWriter
from .theme import Theme


class TeamRosterSheet(SheetWriter):
    """One team's current roster with season per-game averages (one tab per team)."""

    HEADERS = ["Slot", "Player", "NBA Team", "Positions", "Status", "MIN", "FGM", "FGA", "FG%",
               "FTM", "FTA", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
    WIDTHS = [8, 22, 9, 11, 9] + [7.5] * 14
    INVALID_TITLE_CHARS = set("[]:*?/\\")

    def __init__(self, wb, data, stamp, colors, team, title):
        self.team, self.title = team, title
        super().__init__(wb, data, stamp, colors)
        mine = team == data.my_team
        self.TAB_COLOR = Theme.GREEN_TAB if mine else colors.get(team, Theme.MID)

    @classmethod
    def tab_title(cls, team, used):
        """The team's name, made safe for Excel/Sheets: no []:*?/\\, at most 31 characters,
        and unique (case-insensitive) among `used`, which is updated."""
        base = "".join("_" if ch in cls.INVALID_TITLE_CHARS else ch for ch in team).strip("' ") or "Team"
        title, n = base[:31], 2
        while title.lower() in used:
            suffix = f" ({n})"
            title, n = base[:31 - len(suffix)] + suffix, n + 1
        used.add(title.lower())
        return title

    def sheet_title(self):
        return self.title

    def headers(self):
        return self.HEADERS

    def players(self):
        roster = self.data.rosters.get(self.team)
        return roster.in_lineup_order() if roster else []

    def write(self):
        p, n = self.ws, self.ncols
        players = self.players()
        last = self.FIRST + len(players) - 1
        for k, pl in enumerate(players):
            r = self.FIRST + k
            self._write_player(r, pl)
            bg = "FFFFFF" if k % 2 == 0 else "F7F9FC"
            for c in range(1, n + 1):
                p.cell(r, c).fill = Theme.fill(bg)
                p.cell(r, c).border = Border(left=Theme.THICK if c in (6, 13) else Theme.THIN,
                                             right=Theme.THIN, top=Theme.THIN, bottom=Theme.THIN)
            p.row_dimensions[r].height = 21
        self.banner(f"📋  {self.team} ROSTER  ·  Season Averages",
                    f"Updated {self.stamp} from ESPN · FG% and FT% are formulas (made ÷ attempted) · "
                    f"FG%, FT% and TO colored: green = best on team, red = worst")
        self.groups([(1, 5, "PLAYER", Theme.NAVY), (6, 12, "SHOOTING", Theme.MID), (13, 19, "PER GAME", "2E75B6")])
        self.header()
        if players:
            for col, low_good in (("I", False), ("L", False), ("R", True)):
                self.scale(f"{col}{self.FIRST}:{col}{last}", low_good=low_good)
        self.widths(self.WIDTHS)
        p.freeze_panes = "C5"

    def _write_player(self, r, pl):
        p, s = self.ws, pl.stats
        vals = [pl.slot_label, pl.name, pl.nba_team, pl.positions, pl.status,
                s["MIN"], s["FGM"], s["FGA"], None, s["FTM"], s["FTA"], None,
                s["3PM"], s["REB"], s["AST"], s["STL"], s["BLK"], s["TO"], s["PTS"]]
        for c, v in enumerate(vals, 1):
            x = p.cell(r, c, value=v)
            x.font = Theme.VALUE
            x.alignment = Theme.CENTER
            if isinstance(v, (int, float)) and c >= 6:
                x.number_format = "0.0"
        p.cell(r, 9, value=f"=IFERROR(G{r}/H{r},0)").number_format = ".000"
        p.cell(r, 12, value=f"=IFERROR(J{r}/K{r},0)").number_format = ".000"
        for c in (9, 12):
            p.cell(r, c).font = Theme.VALUE
            p.cell(r, c).alignment = Theme.CENTER
        p.cell(r, 1).font = Theme.font(size=10, bold=True, color=Theme.NAVY)
        p.cell(r, 2).font = Theme.font(size=10, bold=True)
        p.cell(r, 2).alignment = Theme.LEFT
        p.cell(r, 5).font = Theme.font(size=10, bold=True, color="C00000")
