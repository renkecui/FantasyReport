"""LeagueData -> styled .xlsx. One SheetWriter subclass per tab."""
from datetime import datetime

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

from .models import CATS


class Theme:
    """Fonts, colors and borders shared by every tab."""
    FONT = "Arial"
    NAVY, MID, GREY, PURP, ORNG = "1F3864", "2F5597", "595959", "7030A0", "C55A11"
    GREEN_TAB = "00873C"  # my team's roster tab
    PALETTE = ["DDEBF7", "FFF2CC", "EDEDED", "E4DFEC", "FCE4D6", "EFE6DA",
               "D9E1F2", "FFE699", "D0CECE", "CCC0DA", "F8CBAD", "E2D5C3"]
    THIN = Side(style="thin", color="D9D9D9")
    THICK = Side(style="medium", color=NAVY)
    CENTER = Alignment(horizontal="center", vertical="center")
    LEFT = Alignment(horizontal="left", vertical="center", indent=1)
    VALUE = Font(name=FONT, size=10, color="000000")  # names and numbers

    @staticmethod
    def fill(color):
        return PatternFill("solid", start_color=color, end_color=color)

    @classmethod
    def font(cls, **kw):
        return Font(name=cls.FONT, **kw)


T = Theme


class SheetWriter:
    """Base class for one tab: title banner, group row, header row, data from row 5."""

    TITLE = ""
    TAB_COLOR = T.MID
    FIRST = 5  # first data row

    def __init__(self, wb, data, stamp, colors, index=None):
        self.data, self.stamp, self.colors = data, stamp, colors
        self.ws = wb.create_sheet(self.sheet_title(), index)

    def sheet_title(self):
        return self.TITLE

    @property
    def ncols(self):
        return len(self.headers())

    def headers(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError

    # ---------------------------------------------------------------- shared styling
    def banner(self, title, sub):
        ws, n = self.ws, self.ncols
        ws.sheet_view.showGridLines = False
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n)
        a = ws.cell(1, 1, value=title)
        a.font = T.font(bold=True, size=16, color="FFFFFF")
        a.alignment = T.LEFT
        for c in range(1, n + 1):
            ws.cell(1, c).fill = T.fill(T.NAVY)
        b = ws.cell(2, 1, value=sub)
        b.font = T.font(italic=True, size=9, color=T.GREY)
        b.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
        ws.row_dimensions[1].height = 34
        ws.row_dimensions[2].height = 30

    def groups(self, spec):
        ws = self.ws
        ws.row_dimensions[3].height = 20
        for s, e, txt, col in spec:
            ws.merge_cells(start_row=3, start_column=s, end_row=3, end_column=e)
            c = ws.cell(3, s, value=txt)
            c.font = T.font(bold=True, size=10, color="FFFFFF")
            c.alignment = T.CENTER
            for k in range(s, e + 1):
                ws.cell(3, k).fill = T.fill(col)
                ws.cell(3, k).border = Border(left=Side(style="thin", color="FFFFFF"),
                                              right=Side(style="thin", color="FFFFFF"))

    def header(self):
        ws = self.ws
        ws.row_dimensions[4].height = 30
        for i, h in enumerate(self.headers(), 1):
            x = ws.cell(4, i, value=h)
            x.font = T.font(bold=True, size=10, color=T.NAVY)
            x.fill = T.fill("D6DCE4")
            x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            x.border = Border(bottom=T.THICK, top=T.THIN, left=T.THIN, right=T.THIN)

    def scale(self, rng, low_good=True):
        a, b = ("63BE7B", "F8696B") if low_good else ("F8696B", "63BE7B")
        self.ws.conditional_formatting.add(rng, ColorScaleRule(
            start_type="min", start_color=a, mid_type="percentile", mid_value=50,
            mid_color="FFEB84", end_type="max", end_color=b))

    def paint(self, r1, r2, seps, color_col, group_col=None):
        """Fill each row with its team's color; thick left border at `seps` columns;
        thick bottom border where the value in `group_col` changes."""
        ws = self.ws
        for r in range(r1, r2 + 1):
            tc = self.colors.get(ws.cell(r, color_col).value, "FFFFFF")
            ws.row_dimensions[r].height = 21
            new_group = (group_col and r < r2
                         and ws.cell(r, group_col).value != ws.cell(r + 1, group_col).value)
            for c in range(1, self.ncols + 1):
                x = ws.cell(r, c)
                x.fill = T.fill(tc)
                if x.alignment.horizontal is None:
                    x.alignment = T.CENTER
                x.border = Border(left=T.THICK if c in seps else T.THIN, right=T.THIN, top=T.THIN,
                                  bottom=T.THICK if new_group else T.THIN)

    def widths(self, widths):
        for i, w in enumerate(widths, 1):
            self.ws.column_dimensions[L(i)].width = w

    def page_setup(self):
        ws = self.ws
        ws.sheet_properties.tabColor = self.TAB_COLOR
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToHeight = 0


class WeeklyStatsSheet(SheetWriter):
    """One row per team per week, with in-week ranks as formulas."""

    TITLE = "Weekly Stats"
    TAB_COLOR = T.MID

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rows = self.data.matchup_rows()
        self.first = self.FIRST
        self.last = self.first + len(self.rows) - 1

    def headers(self):
        return ["Week", "Team", "Opponent", "Cat W", "Cat L", "Cat T", "Result",
                "Avg Rank", "Overall Rank"] + list(CATS) + list(CATS)

    def write(self):
        ws, first, last = self.ws, self.first, self.last
        blocks = []
        for i, (wk, row) in enumerate(self.rows):
            r = first + i
            if not blocks or blocks[-1][0] != wk.number:
                blocks.append([wk.number, r, r])
            blocks[-1][2] = r
            self._write_row(r, wk, row)
        live = self.data.live_weeks
        live_txt = f" · Week {live[0]} is still in progress (Result = Live)" if live else ""
        self.banner("🏀  THE BOYS LEAGUE  ·  Weekly Matchups",
                    f"Updated {self.stamp} from ESPN · Ranks: 1 = best that week (TO: fewest is best) · "
                    f"Overall = week rank by average of the 9 category ranks (lower avg = better){live_txt}")
        self.groups([(1, 7, "MATCHUP", T.NAVY), (8, 9, "OVERALL", T.ORNG),
                     (10, 18, "CATEGORY STATS", T.MID), (19, 27, "WEEKLY RANK  (1 = best)", T.PURP)])
        self.header()
        if self.rows:
            self.paint(first, last, {8, 10, 19}, color_col=2, group_col=1)
            for _, a, b in blocks:
                self.scale(f"S{a}:AA{b}")
                self.scale(f"I{a}:I{b}")
            ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(
                operator="equal", formula=['"W"'], fill=T.fill("C6EFCE"),
                font=T.font(bold=True, color="006100")))
            ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(
                operator="equal", formula=['"L"'], fill=T.fill("FFC7CE"),
                font=T.font(bold=True, color="9C0006")))
        self.widths([7, 24, 24, 7, 7, 7, 8, 9, 10] + [8.5] * 18)
        ws.freeze_panes = "D5"

    def _write_row(self, r, wk, row):
        ws, first, last = self.ws, self.first, self.last
        for c, v in enumerate([wk.number, row.team, row.opponent,
                               row.cat_wins, row.cat_losses, row.cat_ties], 1):
            ws.cell(r, c, value=v).font = T.VALUE
        g = ws.cell(r, 7, value=row.result)
        g.font = T.font(size=10, bold=True)
        if row.decided_by_tiebreak:
            g.comment = Comment("Category tie; the league tiebreaker decided this result.", "Claude")
        ws.cell(r, 8, value=f"=AVERAGE(S{r}:AA{r})").number_format = "0.00"
        ws.cell(r, 8).font = T.font(size=10)
        ws.cell(r, 9, value=f'=COUNTIFS($A${first}:$A${last},$A{r},$H${first}:$H${last},"<"&H{r})+1'
                ).font = T.font(size=11, bold=True)
        for j, cat in enumerate(CATS):
            x = ws.cell(r, 10 + j, value=row.stats[cat])
            x.font = T.VALUE
            x.number_format = ".0000" if j < 2 else "#,##0"
        for j, cat in enumerate(CATS):
            sc = L(10 + j)
            op = "<" if cat == "TO" else ">"
            ws.cell(r, 19 + j,
                    value=f'=COUNTIFS($A${first}:$A${last},$A{r},{sc}${first}:{sc}${last},"{op}"&{sc}{r})+1'
                    ).font = T.font(size=10, bold=True)
        ws.cell(r, 2).font = T.font(size=10, bold=True)
        ws.cell(r, 2).alignment = T.LEFT
        ws.cell(r, 3).alignment = T.LEFT


class SeasonTotalsSheet(SheetWriter):
    """One row per team; every number is a formula over the Weekly Stats tab."""

    TITLE = "Season Totals"
    TAB_COLOR = T.PURP

    def __init__(self, wb, data, stamp, colors, weekly, index=None):
        super().__init__(wb, data, stamp, colors, index)
        self.weekly = weekly

    def headers(self):
        return ["Team", "Matchup W", "Matchup L", "Matchup T", "Record", "Cat W", "Cat L", "Cat T"] \
            + list(CATS) + list(CATS)

    def _rng(self, col):
        w = self.weekly
        return f"'{w.TITLE}'!${col}${w.first}:${col}${w.last}"

    def write(self):
        t, rng = self.ws, self._rng
        teams = self.data.teams_mine_first()
        tl = 4 + len(teams)
        for k, tm in enumerate(teams):
            r = 5 + k
            t.cell(r, 1, value=tm).font = T.font(size=10, bold=True)
            t.cell(r, 1).alignment = T.LEFT
            for c, res in ((2, "W"), (3, "L"), (4, "T")):
                t.cell(r, c, value=f'=COUNTIFS({rng("B")},$A{r},{rng("G")},"{res}")')
            t.cell(r, 5, value=f'=B{r}&"-"&C{r}&"-"&D{r}').font = T.font(size=11, bold=True)
            for c, col in zip((6, 7, 8), ("D", "E", "F")):
                t.cell(r, c, value=f'=SUMIFS({rng(col)},{rng("B")},$A{r})')
            for j in range(9):
                col = L(10 + j)
                fn = "AVERAGEIFS" if j < 2 else "SUMIFS"
                x = t.cell(r, 9 + j, value=f'={fn}({rng(col)},{rng("B")},$A{r})')
                x.number_format = ".0000" if j < 2 else "#,##0"
            for j in range(9):
                sc = L(9 + j)
                t.cell(r, 18 + j, value=f'=RANK({sc}{r},${sc}$5:${sc}${tl},{1 if CATS[j] == "TO" else 0})'
                       ).font = T.font(size=10, bold=True)
            for c in list(range(2, 5)) + list(range(6, 18)):
                t.cell(r, c).font = T.font(size=10)
        self.banner(f"🏆  SEASON TOTALS  ·  Weeks 1-{len(self.data.weeks)}",
                    f"Updated {self.stamp} from ESPN · Counting stats are summed; FG% and FT% are averages "
                    f"of weekly %. Record counts finished weeks only; stats include any week in progress. "
                    f"Rank 1 = best (TO: fewest is best).")
        self.groups([(1, 8, "RECORD", T.NAVY), (9, 17, "SEASON STATS", T.MID),
                     (18, 26, "LEAGUE RANK  (1 = best)", T.PURP)])
        self.header()
        self.paint(5, tl, {9, 18}, color_col=1)
        for r in range(5, tl + 1):
            t.row_dimensions[r].height = 24
        self.scale(f"R5:Z{tl}")
        self.widths([24, 9, 9, 9, 10, 7, 7, 7] + [9] * 18)
        t.freeze_panes = "B5"




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
        self.TAB_COLOR = T.GREEN_TAB if mine else colors.get(team, T.MID)

    @classmethod
    def tab_title(cls, team, used):
        """'<team> Roster', made safe for Excel/Sheets: no []:*?/\\, at most 31 characters,
        and unique (case-insensitive) among `used`, which is updated."""
        clean = "".join("_" if ch in cls.INVALID_TITLE_CHARS else ch for ch in team).strip("' ") or "Team"
        base = f"{clean} Roster"
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
                p.cell(r, c).fill = T.fill(bg)
                p.cell(r, c).border = Border(left=T.THICK if c in (6, 13) else T.THIN,
                                             right=T.THIN, top=T.THIN, bottom=T.THIN)
            p.row_dimensions[r].height = 21
        self.banner(f"📋  {self.team} ROSTER  ·  Season Averages",
                    f"Updated {self.stamp} from ESPN · FG% and FT% are formulas (made ÷ attempted) · "
                    f"FG%, FT% and TO colored: green = best on team, red = worst")
        self.groups([(1, 5, "PLAYER", T.NAVY), (6, 12, "SHOOTING", T.MID), (13, 19, "PER GAME", "2E75B6")])
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
            x.font = T.VALUE
            x.alignment = T.CENTER
            if isinstance(v, (int, float)) and c >= 6:
                x.number_format = "0.0"
        p.cell(r, 9, value=f"=IFERROR(G{r}/H{r},0)").number_format = ".000"
        p.cell(r, 12, value=f"=IFERROR(J{r}/K{r},0)").number_format = ".000"
        for c in (9, 12):
            p.cell(r, c).font = T.VALUE
            p.cell(r, c).alignment = T.CENTER
        p.cell(r, 1).font = T.font(size=10, bold=True, color=T.NAVY)
        p.cell(r, 2).font = T.font(size=10, bold=True)
        p.cell(r, 2).alignment = T.LEFT
        p.cell(r, 5).font = T.font(size=10, bold=True, color="C00000")


class WorkbookBuilder:
    """Builds the whole workbook: Season Totals, Weekly Stats, then one roster tab per team
    (my team first)."""

    def __init__(self, data, now=None):
        self.data = data
        self.stamp = (now or datetime.now()).strftime("%b %d, %Y %I:%M %p")
        self.colors = {t: T.PALETTE[i % len(T.PALETTE)] for i, t in enumerate(data.teams_mine_first())}

    def build(self):
        wb = Workbook()
        wb.remove(wb.active)
        args = (wb, self.data, self.stamp, self.colors)
        weekly = WeeklyStatsSheet(*args)
        sheets = [SeasonTotalsSheet(*args, weekly=weekly, index=0), weekly]
        used = {SeasonTotalsSheet.TITLE.lower(), WeeklyStatsSheet.TITLE.lower()}
        for team in self.data.teams_mine_first():
            sheets.append(TeamRosterSheet(*args, team=team, title=TeamRosterSheet.tab_title(team, used)))
        for sheet in sheets:
            sheet.write()
            sheet.page_setup()
        wb.active = 0
        return wb

    def save(self, path):
        self.build().save(path)
