from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter as L

from .sheet_writer import SheetWriter
from .theme import Theme
from ..models.categories import Categories


class WeeklyStatsSheet(SheetWriter):
    """One row per team per week, with in-week ranks as formulas."""

    TITLE = "Weekly Stats"
    TAB_COLOR = Theme.MID

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rows = self.data.matchup_rows()
        self.first = self.FIRST
        self.last = self.first + len(self.rows) - 1

    def headers(self):
        return ["Week", "Team", "Opponent", "Cat W", "Cat L", "Cat T", "Result",
                "Avg Rank", "Overall Rank"] + list(Categories.ALL) + list(Categories.ALL)

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
        self.groups([(1, 7, "MATCHUP", Theme.NAVY), (8, 9, "OVERALL", Theme.ORNG),
                     (10, 18, "CATEGORY STATS", Theme.MID), (19, 27, "WEEKLY RANK  (1 = best)", Theme.PURP)])
        self.header()
        if self.rows:
            self.paint(first, last, {8, 10, 19}, color_col=2, group_col=1)
            for _, a, b in blocks:
                self.scale(f"S{a}:AA{b}")
                self.scale(f"I{a}:I{b}")
            ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(
                operator="equal", formula=['"W"'], fill=Theme.fill("C6EFCE"),
                font=Theme.font(bold=True, color="006100")))
            ws.conditional_formatting.add(f"G{first}:G{last}", CellIsRule(
                operator="equal", formula=['"L"'], fill=Theme.fill("FFC7CE"),
                font=Theme.font(bold=True, color="9C0006")))
        self.widths([7, 24, 24, 7, 7, 7, 8, 9, 10] + [8.5] * 18)
        ws.freeze_panes = "D5"

    def _write_row(self, r, wk, row):
        ws, first, last = self.ws, self.first, self.last
        for c, v in enumerate([wk.number, row.team, row.opponent,
                               row.cat_wins, row.cat_losses, row.cat_ties], 1):
            ws.cell(r, c, value=v).font = Theme.VALUE
        g = ws.cell(r, 7, value=row.result)
        g.font = Theme.font(size=10, bold=True)
        if row.decided_by_tiebreak:
            g.comment = Comment("Category tie; the league tiebreaker decided this result.", "Claude")
        ws.cell(r, 8, value=f"=AVERAGE(S{r}:AA{r})").number_format = "0.00"
        ws.cell(r, 8).font = Theme.font(size=10)
        ws.cell(r, 9, value=f'=COUNTIFS($A${first}:$A${last},$A{r},$H${first}:$H${last},"<"&H{r})+1'
                ).font = Theme.font(size=11, bold=True)
        for j, cat in enumerate(Categories.ALL):
            x = ws.cell(r, 10 + j, value=row.stats[cat])
            x.font = Theme.VALUE
            x.number_format = ".0000" if j < 2 else "#,##0"
        for j, cat in enumerate(Categories.ALL):
            sc = L(10 + j)
            op = "<" if cat == "TO" else ">"
            ws.cell(r, 19 + j,
                    value=f'=COUNTIFS($A${first}:$A${last},$A{r},{sc}${first}:{sc}${last},"{op}"&{sc}{r})+1'
                    ).font = Theme.font(size=10, bold=True)
        ws.cell(r, 2).font = Theme.font(size=10, bold=True)
        ws.cell(r, 2).alignment = Theme.LEFT
        ws.cell(r, 3).alignment = Theme.LEFT
