from openpyxl.utils import get_column_letter as L

from .sheet_writer import SheetWriter
from .theme import Theme
from ..models.categories import Categories


class SeasonTotalsSheet(SheetWriter):
    """One row per team; every number is a formula over the Weekly Stats tab."""

    TITLE = "Season Totals"
    TAB_COLOR = Theme.PURP

    def __init__(self, wb, data, stamp, colors, weekly, index=None):
        super().__init__(wb, data, stamp, colors, index)
        self.weekly = weekly

    def headers(self):
        return ["Team", "Matchup W", "Matchup L", "Matchup T", "Record", "Cat W", "Cat L", "Cat T"] \
            + list(Categories.ALL) + list(Categories.ALL)

    def _rng(self, col):
        w = self.weekly
        return f"'{w.TITLE}'!${col}${w.first}:${col}${w.last}"

    def write(self):
        t, rng = self.ws, self._rng
        teams = self.data.teams_mine_first()
        tl = 4 + len(teams)
        for k, tm in enumerate(teams):
            r = 5 + k
            t.cell(r, 1, value=tm).font = Theme.font(size=10, bold=True)
            t.cell(r, 1).alignment = Theme.LEFT
            for c, res in ((2, "W"), (3, "L"), (4, "T")):
                t.cell(r, c, value=f'=COUNTIFS({rng("B")},$A{r},{rng("G")},"{res}")')
            t.cell(r, 5, value=f'=B{r}&"-"&C{r}&"-"&D{r}').font = Theme.font(size=11, bold=True)
            for c, col in zip((6, 7, 8), ("D", "E", "F")):
                t.cell(r, c, value=f'=SUMIFS({rng(col)},{rng("B")},$A{r})')
            for j in range(9):
                col = L(10 + j)
                fn = "AVERAGEIFS" if j < 2 else "SUMIFS"
                x = t.cell(r, 9 + j, value=f'={fn}({rng(col)},{rng("B")},$A{r})')
                x.number_format = ".0000" if j < 2 else "#,##0"
            for j in range(9):
                sc = L(9 + j)
                t.cell(r, 18 + j, value=f'=RANK({sc}{r},${sc}$5:${sc}${tl},{1 if Categories.ALL[j] == "TO" else 0})'
                       ).font = Theme.font(size=10, bold=True)
            for c in list(range(2, 5)) + list(range(6, 18)):
                t.cell(r, c).font = Theme.font(size=10)
        self.banner(f"🏆  SEASON TOTALS  ·  Weeks 1-{len(self.data.weeks)}",
                    f"Updated {self.stamp} from ESPN · Counting stats are summed; FG% and FT% are averages "
                    f"of weekly %. Record counts finished weeks only; stats include any week in progress. "
                    f"Rank 1 = best (TO: fewest is best).")
        self.groups([(1, 8, "RECORD", Theme.NAVY), (9, 17, "SEASON STATS", Theme.MID),
                     (18, 26, "LEAGUE RANK  (1 = best)", Theme.PURP)])
        self.header()
        self.paint(5, tl, {9, 18}, color_col=1)
        for r in range(5, tl + 1):
            t.row_dimensions[r].height = 24
        self.scale(f"R5:Z{tl}")
        self.widths([24, 9, 9, 9, 10, 7, 7, 7] + [9] * 18)
        t.freeze_panes = "B5"
